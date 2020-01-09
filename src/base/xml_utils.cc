#include "xml_utils.h"

#include "persistent-data/file_utils.h"
#include <fstream>
#include <iostream>

using namespace xml_utils;

//----------------------------------------------------------------

void
xml_parser::parse(std::string const &backup_file, bool quiet)
{
	persistent_data::check_file_exists(backup_file);
	ifstream in(backup_file.c_str(), ifstream::in);

	std::auto_ptr<base::progress_monitor> monitor = create_monitor(quiet);

	size_t total = 0;
	size_t input_length = get_file_length(backup_file);

	while (!in.eof()) {
		char buffer[4096];
		in.read(buffer, sizeof(buffer));
		size_t len = in.gcount();
		int done = in.eof();

		if (!XML_Parse(parser_, buffer, len, done)) {
			ostringstream out;
			out << "Parse error at line "
			    << XML_GetCurrentLineNumber(parser_)
			    << ":\n"
			    << XML_ErrorString(XML_GetErrorCode(parser_))
			    << endl;
			throw runtime_error(out.str());
		}

		total += len;
		monitor->update_percent(total * 100 / input_length);
	}
}

size_t
xml_parser::get_file_length(string const &file) const
{
	struct stat info;
	int r;

	r = ::stat(file.c_str(), &info);
	if (r)
		throw runtime_error("Couldn't stat backup path");

	return info.st_size;
}

auto_ptr<base::progress_monitor>
xml_parser::create_monitor(bool quiet)
{
	if (!quiet && isatty(fileno(stdout)))
		return base::create_progress_bar("Restoring");
	else
		return base::create_quiet_progress_monitor();
}

//----------------------------------------------------------------

void
xml_utils::build_attributes(attributes &a, char const **attr)
{
	while (*attr) {
		char const *key = *attr;

		attr++;
		if (!*attr) {
			ostringstream out;
			out << "No value given for xml attribute: " << key;
			throw runtime_error(out.str());
		}

		char const *value = *attr;
		a.insert(make_pair(string(key), string(value)));
		attr++;
	}
}

//----------------------------------------------------------------
