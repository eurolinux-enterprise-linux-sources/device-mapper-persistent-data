#include "block-cache/block_cache.h"

#include <algorithm>
#include <assert.h>
#include <libaio.h>
#include <errno.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <iostream>
#include <stdexcept>
#include <sstream>

using namespace bcache;

//----------------------------------------------------------------

// FIXME: get from linux headers
#define SECTOR_SHIFT 9
#define PAGE_SIZE 4096

#define MIN_BLOCKS 16
#define WRITEBACK_LOW_THRESHOLD_PERCENT 33
#define WRITEBACK_HIGH_THRESHOLD_PERCENT 66

//----------------------------------------------------------------

namespace {
	void *alloc_aligned(size_t len, size_t alignment)
	{
		void *result = NULL;
		int r = posix_memalign(&result, alignment, len);
		if (r)
			return NULL;

		return result;
	}
}

//----------------------------------------------------------------

int
block_cache::init_free_list(unsigned count)
{
	size_t block_size = block_size_ << SECTOR_SHIFT;
	unsigned char *data = static_cast<unsigned char *>(alloc_aligned(count * block_size, PAGE_SIZE));

	/* Allocate the data for each block.  We page align the data. */
	if (!data)
		return -ENOMEM;

	blocks_data_ = data;

	for (unsigned i = 0; i < count; i++) {
		block &b = (*blocks_memory_)[i];
		b.data_ = data + (block_size * i);
		free_.push_front(b);
	}

	return 0;
}

void
block_cache::exit_free_list()
{
	if (blocks_data_)
		free(blocks_data_);
}

block_cache::block *
block_cache::__alloc_block()
{
	if (free_.empty())
		return NULL;

	block &b = free_.front();
	b.unlink();

	return &b;
}

/*----------------------------------------------------------------
 * Low level IO handling
 *
 * We cannot have two concurrent writes on the same block.
 * eg, background writeback, put with dirty, flush?
 *
 * To avoid this we introduce some restrictions:
 *
 * i)  A held block can never be written back.
 * ii) You cannot get a block until writeback has completed.
 *
 *--------------------------------------------------------------*/

/*
 * This can be called from the context of the aio thread.  So we have a
 * separate 'top half' complete function that we know is only called by the
 * main cache thread.
 */
void
block_cache::complete_io(block &b, int result)
{
	b.error_ = result;
	b.clear_flags(BF_IO_PENDING);
	nr_io_pending_--;

	if (b.error_) {
		b.unlink();
		errored_.push_back(b);

	} else {
		if (b.test_flags(BF_DIRTY)) {
			b.clear_flags(BF_DIRTY | BF_PREVIOUSLY_DIRTY);
			nr_dirty_--;
		}

		b.unlink();
		clean_.push_back(b);
	}
}

/*
 * |b->list| should be valid (either pointing to itself, on one of the other
 * lists.
 */
// FIXME: add batch issue
void
block_cache::issue_low_level(block &b, enum io_iocb_cmd opcode, const char *desc)
{
	int r;
	iocb *control_blocks[1];

	assert(!b.test_flags(BF_IO_PENDING));
	b.set_flags(BF_IO_PENDING);
	nr_io_pending_++;
	b.unlink();
	io_pending_.push_back(b);

	b.control_block_.aio_lio_opcode = opcode;
	control_blocks[0] = &b.control_block_;
	r = io_submit(aio_context_, 1, control_blocks);
	if (r != 1) {
		complete_io(b, EIO);

		std::ostringstream out;
		out << "couldn't issue " << desc << " io for block " << b.index_;

		if (r < 0)
			out << ": io_submit failed with " << r;
		else
			out << ": io_submit succeeded, but queued no io";

		throw std::runtime_error(out.str());
	}
}

void
block_cache::issue_read(block &b)
{
	assert(!b.test_flags(BF_IO_PENDING));
	issue_low_level(b, IO_CMD_PREAD, "read");
}

void
block_cache::issue_write(block &b)
{
	assert(!b.test_flags(BF_IO_PENDING));
	b.v_->prepare(b.data_, b.index_);
	issue_low_level(b, IO_CMD_PWRITE, "write");
}

void
block_cache::wait_io()
{
	int r;
	unsigned i;

	// FIXME: use a timeout to prevent hanging
	r = io_getevents(aio_context_, 1, nr_cache_blocks_, &events_[0], NULL);
	if (r < 0) {
		std::ostringstream out;
		out << "io_getevents failed: " << r;
		throw std::runtime_error(out.str());
	}

	for (i = 0; i < static_cast<unsigned>(r); i++) {
		io_event const &e = events_[i];
		block *b = base::container_of(e.obj, &block::control_block_);

		if (e.res == block_size_ << SECTOR_SHIFT)
			complete_io(*b, 0);

		else if (static_cast<long>(e.res) < 0)
			complete_io(*b, e.res);

		else {
			std::ostringstream out;
			out << "incomplete io for block " << b->index_
			    << ", e.res = " << e.res
			    << ", e.res2 = " << e.res2
			    << ", offset = " << b->control_block_.u.c.offset
			    << ", nbytes = " << b->control_block_.u.c.nbytes;
			throw std::runtime_error(out.str());
		}
	}
}

/*----------------------------------------------------------------
 * Clean/dirty list management
 *--------------------------------------------------------------*/

/*
 * We're using lru lists atm, but I think it would be worth
 * experimenting with a multiqueue approach.
 */
block_cache::block_list &
block_cache::__categorise(block &b)
{
	if (b.error_)
		return errored_;

	return b.test_flags(BF_DIRTY) ? dirty_ : clean_;
}

void
block_cache::hit(block &b)
{
	b.unlink();
	__categorise(b).push_back(b);
}

/*----------------------------------------------------------------
 * High level IO handling
 *--------------------------------------------------------------*/
void
block_cache::wait_all()
{
	while (!io_pending_.empty())
		wait_io();
}

void
block_cache::wait_specific(block &b)
{
	while (b.test_flags(BF_IO_PENDING))
		wait_io();
}

unsigned
block_cache::writeback(unsigned count)
{
	unsigned actual = 0, dirty_length = 0;

	// issue_write unlinks b, which invalidates the iteration, so we
	// keep track of the next element before removing.
	auto it = dirty_.begin();
	auto next = it;
	while (it != dirty_.end()) {
		next = it;
		++next;
		dirty_length++;

		if (actual == count)
			break;

		// The block may be on the dirty list from a prior
		// acquisition.
		if (it->ref_count_)
			continue;

		issue_write(*it);
		actual++;

		it = next;
	}

	return actual;
}

/*----------------------------------------------------------------
 * High level allocation
 *--------------------------------------------------------------*/
void
block_cache::setup_control_block(block &b)
{
	iocb *cb = &b.control_block_;
	size_t block_size_bytes = block_size_ << SECTOR_SHIFT;

	memset(cb, 0, sizeof(*cb));
	cb->aio_fildes = fd_;

	cb->u.c.buf = b.data_;
	cb->u.c.offset = block_size_bytes * b.index_;
	cb->u.c.nbytes = block_size_bytes;
}

// FIXME: return a reference
block_cache::block *
block_cache::find_unused_clean_block()
{
	for (block &b : clean_) {
		if (b.ref_count_)
			continue;

		b.unlink_set();
		b.unlink();
		return &b;
	}

	return NULL;
}

block_cache::block *
block_cache::new_block(block_address index)
{
	block *b;

	b = __alloc_block();
	if (!b) {
		if (clean_.empty()) {
			if (io_pending_.empty())
				writeback(16);
			wait_io();
		}

		b = find_unused_clean_block();
	}

	if (b) {
		b->bc_ = this;
		b->ref_count_ = 0;

		b->error_ = 0;
		b->flags_ = 0;
		b->v_ = noop_validator_;

		b->index_ = index;
		setup_control_block(*b);

		block_set_.insert(*b);
	}

	return b;
}

/*----------------------------------------------------------------
 * Block reference counting
 *--------------------------------------------------------------*/
unsigned
block_cache::calc_nr_cache_blocks(size_t mem, sector_t block_size)
{
	size_t space_per_block = (block_size << SECTOR_SHIFT) + sizeof(block);
	unsigned r = mem / space_per_block;

	return (r < MIN_BLOCKS) ? MIN_BLOCKS : r;
}

unsigned
block_cache::calc_nr_buckets(unsigned nr_blocks)
{
	unsigned r = 8;
	unsigned n = nr_blocks / 4;

	if (n < 8)
		n = 8;

	while (r < n)
		r <<= 1;

	return r;
}

block_cache::block_cache(int fd, sector_t block_size, uint64_t on_disk_blocks, size_t mem)
	: nr_locked_(0),
	  nr_dirty_(0),
	  nr_io_pending_(0),
	  read_hits_(0),
	  read_misses_(0),
	  write_zeroes_(0),
	  write_hits_(0),
	  write_misses_(0),
	  prefetches_(0),
	  noop_validator_(new noop_validator())
{
	int r;
	unsigned nr_cache_blocks = calc_nr_cache_blocks(mem, block_size);

	fd_ = fd;
	block_size_ = block_size;
	nr_data_blocks_ = on_disk_blocks;
	nr_cache_blocks_ = nr_cache_blocks;

	events_.resize(nr_cache_blocks);

	aio_context_ = 0; /* needed or io_setup will fail */
	r = io_setup(nr_cache_blocks, &aio_context_);
	if (r < 0) {
		perror("io_setup failed");
		throw std::runtime_error("io_setup failed");
	}

	blocks_memory_.reset(new std::vector<block>(nr_cache_blocks));

	r = init_free_list(nr_cache_blocks);
	if (r)
		throw std::runtime_error("couldn't allocate blocks");
}

block_cache::~block_cache()
{
	assert(!nr_locked_);
	flush();
	wait_all();

	exit_free_list();

	if (aio_context_)
		io_destroy(aio_context_);

	::close(fd_);

#if 0
	std::cerr << "\nblock cache stats\n"
		  << "=================\n"
		  << "prefetches:\t" << prefetches_ << "\n"
		  << "read hits:\t" << read_hits_ << "\n"
		  << "read misses:\t" << read_misses_ << "\n"
		  << "write hits:\t" << write_hits_ << "\n"
		  << "write misses:\t" << write_misses_ << "\n"
		  << "write zeroes:\t" << write_zeroes_ << std::endl;
#endif
}

uint64_t
block_cache::get_nr_blocks() const
{
	return nr_data_blocks_;
}

uint64_t
block_cache::get_nr_locked() const
{
	return nr_locked_;
}

void
block_cache::zero_block(block &b)
{
	write_zeroes_++;
	memset(b.data_, 0, block_size_ << SECTOR_SHIFT);
	b.mark_dirty();
}

void
block_cache::inc_hit_counter(unsigned flags)
{
	if (flags & (GF_ZERO | GF_DIRTY))
		write_hits_++;
	else
		read_hits_++;
}

void
block_cache::inc_miss_counter(unsigned flags)
{
	if (flags & (GF_ZERO | GF_DIRTY))
		write_misses_++;
	else
		read_misses_++;
}

block_cache::block *
block_cache::lookup_or_read_block(block_address index, unsigned flags,
				  validator::ptr v)
{
	auto it = block_set_.find(index, cmp_index());

	if (it != block_set_.end()) {
		if (it->test_flags(BF_IO_PENDING)) {
			inc_miss_counter(flags);
			wait_specific(*it);
		} else
			inc_hit_counter(flags);

		if (flags & GF_ZERO)
			zero_block(*it);
		else {
			if (it->v_.get() != v.get()) {
				if (it->test_flags(BF_DIRTY))
					it->v_->prepare(it->data_, it->index_);
				v->check(it->data_, it->index_);
			}
		}
		it->v_ = v;
		return &(*it);

	} else {
		inc_miss_counter(flags);

		block *b = new_block(index);
		if (b) {
			if (flags & GF_ZERO)
				zero_block(*b);
			else {
				issue_read(*b);
				wait_specific(*b);
				v->check(b->data_, b->index_);
			}

			b->v_ = v;
		}

		return (!b || b->error_) ? NULL : b;
	}
}

block_cache::block &
block_cache::get(block_address index, unsigned flags, validator::ptr v)
{
	check_index(index);

	block *b = lookup_or_read_block(index, flags, v);

	if (b) {
		if (b->ref_count_ && (flags & (GF_DIRTY | GF_ZERO))) {
			std::ostringstream out;
			out << "attempt to write lock block " << index << " concurrently";
			throw std::runtime_error(out.str());
		}

		// FIXME: this gets called even for new blocks
		hit(*b);

		if (!b->ref_count_)
			nr_locked_++;

		b->ref_count_++;

		if (flags & GF_BARRIER)
			b->set_flags(BF_FLUSH);

		if (flags & GF_DIRTY)
			b->set_flags(BF_DIRTY);

		return *b;
	}

	std::ostringstream out;
	out << "couldn't get block " << index;
	throw std::runtime_error(out.str());
}

void
block_cache::preemptive_writeback()
{
	unsigned nr_available = nr_cache_blocks_ - (nr_dirty_ - nr_io_pending_);
	if (nr_available < (WRITEBACK_LOW_THRESHOLD_PERCENT * nr_cache_blocks_ / 100))
		writeback((WRITEBACK_HIGH_THRESHOLD_PERCENT * nr_cache_blocks_ / 100) - nr_available);

}

void
block_cache::release(block_cache::block &b)
{
	assert(!b.ref_count_);

	nr_locked_--;

	if (b.test_flags(BF_FLUSH))
		flush();

	if (b.test_flags(BF_DIRTY)) {
		if (!b.test_flags(BF_PREVIOUSLY_DIRTY)) {
			b.unlink();
			dirty_.push_back(b);
			nr_dirty_++;
			b.set_flags(BF_PREVIOUSLY_DIRTY);
		}

		if (b.test_flags(BF_FLUSH))
			flush();
		else
			preemptive_writeback();

		b.clear_flags(BF_FLUSH);
	}
}

int
block_cache::flush()
{
	while (!dirty_.empty()) {
		block &b = dirty_.front();
		if (b.ref_count_ || b.test_flags(BF_IO_PENDING))
			// The superblock may well be still locked.
			continue;

		issue_write(b);
	}

	wait_all();

	return errored_.empty() ? 0 : -EIO;
}

void
block_cache::prefetch(block_address index)
{
	check_index(index);

	auto it = block_set_.find(index, cmp_index());

	if (it == block_set_.end()) {
		prefetches_++;

		block *b = new_block(index);
		if (b)
			issue_read(*b);
	}
}

void
block_cache::check_index(block_address index) const
{
	if (index >= nr_data_blocks_) {
		std::ostringstream out;
		out << "block out of bounds ("
		    << index << " >= " << nr_data_blocks_ << ")\n";
		throw std::runtime_error(out.str());
	}
}

//----------------------------------------------------------------
