#
# Copyright (C) 2011-2017 Red Hat, Inc
#

Summary: Device-mapper Persistent Data Tools
Name: device-mapper-persistent-data
Version: 0.7.3
Release: 3%{?dist}
License: GPLv3+
Group: System Environment/Base
URL: https://github.com/jthornber/thin-provisioning-tools
#Source0: https://github.com/jthornber/thin-provisioning-tools/archive/thin-provisioning-tools-% {version}.tar.gz
Source0: https://github.com/jthornber/thin-provisioning-tools/archive/v%{version}.tar.gz
Patch0: device-mapper-persistent-data-avoid-strip.patch
Patch1: device-mapper-persistent-data-cache_restore-v2-dirty-bitset.patch

BuildRequires: autoconf, expat-devel, libaio-devel, libstdc++-devel, boost-devel
Requires: expat

%description
thin-provisioning-tools contains check,dump,restore,repair,rmap
and metadata_size tools to manage device-mapper thin provisioning
target metadata devices; cache check,dump,metadata_size,restore
and repair tools to manage device-mapper cache metadata devices
are included and era check, dump, restore and invalidate to manage
snapshot eras

%prep
%setup -q -n thin-provisioning-tools-%{version}
%patch0 -p1 -b .avoid_strip
%patch1 -p1 -b .v2_dirty_bitset
echo %{version}-%{release} > VERSION

%build
autoconf
%configure --with-optimisation=
make %{?_smp_mflags} V=

%install
make DESTDIR=%{buildroot} MANDIR=%{_mandir} install

%clean

%files
%doc COPYING README.md
%{_mandir}/man8/cache_check.8.gz
%{_mandir}/man8/cache_dump.8.gz
%{_mandir}/man8/cache_metadata_size.8.gz
%{_mandir}/man8/cache_repair.8.gz
%{_mandir}/man8/cache_restore.8.gz
%{_mandir}/man8/cache_writeback.8.gz
%{_mandir}/man8/era_check.8.gz
%{_mandir}/man8/era_dump.8.gz
%{_mandir}/man8/era_invalidate.8.gz
%{_mandir}/man8/era_restore.8.gz
%{_mandir}/man8/thin_check.8.gz
%{_mandir}/man8/thin_delta.8.gz
%{_mandir}/man8/thin_dump.8.gz
%{_mandir}/man8/thin_ls.8.gz
%{_mandir}/man8/thin_metadata_size.8.gz
%{_mandir}/man8/thin_repair.8.gz
%{_mandir}/man8/thin_restore.8.gz
%{_mandir}/man8/thin_rmap.8.gz
%{_mandir}/man8/thin_trim.8.gz
%{_sbindir}/pdata_tools
%{_sbindir}/cache_check
%{_sbindir}/cache_dump
%{_sbindir}/cache_metadata_size
%{_sbindir}/cache_repair
%{_sbindir}/cache_restore
%{_sbindir}/cache_writeback
%{_sbindir}/era_check
%{_sbindir}/era_dump
%{_sbindir}/era_invalidate
%{_sbindir}/era_restore
%{_sbindir}/thin_check
%{_sbindir}/thin_delta
%{_sbindir}/thin_dump
%{_sbindir}/thin_ls
%{_sbindir}/thin_metadata_size
%{_sbindir}/thin_repair
%{_sbindir}/thin_restore
%{_sbindir}/thin_rmap
%{_sbindir}/thin_trim

%changelog
* Tue Nov 14 2017 Marian Csontos <mcsontos@redhat.com> - 0.7.3-3
- Fix version 2 metadata corruption in cache_restore.

* Tue Oct 10 2017 Marian Csontos <mcsontos@redhat.com> - 0.7.3-2
- Rebuilding with updated source tarball.

* Fri Oct 06 2017 Marian Csontos <mcsontos@redhat.com> - 0.7.3-1
- Update to latest bugfix and documentation update release.
- *_restore tools wipe superblock as a last resort.
- Add thin_check --override-mapping-root.

* Fri Sep 22 2017 Marian Csontos <mcsontos@redhat.com> - 0.7.2-1
- Update to latest upstream release including various bug fixes and new features.
- Fix segfault when dump tools are given a tiny metadata file.
- Fix -V exiting with 1.
- Fix thin_check when running on XML dump instead of binary data.
- Speed up free block searches.

* Mon Mar 27 2017 Peter Rajnoha <prajnoha@redhat.com> - 0.7.0-0.1-rc6
- Don't open devices as writeable if --clear-needs-check-flag is not set.
- Fix cache metadata format version 2 superblock packing.

* Wed Mar 22 2017 Peter Rajnoha <prajnoha@redhat.com> - 0.7.0-0.1-rc5
- Switch to a faster implementation of crc32 used for checksums.

* Tue Mar 21 2017 Peter Rajnoha <prajnoha@redhat.com> - 0.7.0-0.1-rc4
- Add support for cache metadata format version 2 in cache tools.

* Thu Mar 16 2017 Peter Rajnoha <prajnoha@redhat.com> - 0.7.0-0.1-rc3
- Update to latest upstream release including various bug fixes and new features.
- New thin_show_duplicates command.
- Add '--skip-mappings' and '--format custom' options to thin_dump.

* Fri Jul 22 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.3-1
- Fix regression in thin_repair and thin_restore so it works again
  when using device as output.

* Thu Jul 21 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-2
- Improve documentation and messages on output file preallocation
  when using thin_repair and thin_restore.

* Mon Jul 11 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-1
- Fixes providing proper use of compiler flags.

* Wed May 04 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-0.1.rc8
- Fixes for thin_trim and thin_repair.

* Wed Mar 09 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-0.1.rc6
- Add new fields to thin_ls: MAPPED_BYTES, EXCLUSIVE_BYTES and SHARED_BYTES.

* Tue Mar 08 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-0.1.rc5
- New thin_ls command.
- era_invalidate may be run on live metadata if the --metadata-snap
  option is given.

* Thu Aug 13 2015 Peter Rajnoha <prajnoha@redhat.com> - 0.5.5-1
- Support thin_delta's --metadata_snap option without specifying snap location.
- Update man pages to make it clearer that tools shoulnd't be run on live metadata.
- Fix bugs in the metadata reference counting for thin_check.

* Fri Jul 17 2015 Peter Rajnoha <prajnoha@redhat.com> - 0.5.4-1
- Fix cache_check with --clear-needs-check-flag option to
  make sure metadata device is not open already by the tool
  when open with O_EXCL mode is requested.

* Tue Jul 07 2015 Peter Rajnoha <prajnoha@redhat.com> - 0.5.3-1
- Tools now open the metadata device in O_EXCL mode to stop
  running the tools on active metadata.
- Update to latest upstream release.

* Fri Jul 03 2015 Peter Rajnoha <prajnoha@redhat.com> - 0.5.2-1
- Fix bug in damage reporting in thin_dump and thin_check.
- Update to latest upstream release.

* Thu Jun 25 2015 Peter Rajnoha <prajnoha@redhat.com> - 0.5.1-1
- Add space map checking for thin_check.
- Add --clear-needs-check option for cache_check.
- Update to latest upstream release.

* Mon Jun 08 2015 Peter Rajnoha <prajnoha@redhat.com> - 0.4.2-1
- New thin_delta and thin_trim commands.
- Update to latest upstream release.

* Wed Nov 12 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.4.1-2
- Resolves: #1083394
- Resolves: #1085620
- Fixes empty debuginfo packages

* Tue Oct 28 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.4.1-1
- Resolves: #1083394
- Resolves: #1085620

* Wed Apr 2 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.3.2-1
- Resolves: #1081546

* Fri Mar 28 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.3.0-1
- Resolves: #1081546

* Fri Feb 28 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-5
- Resolves: #1057951

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.2.8-4
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.2.8-3
- Mass rebuild 2013-12-27

* Wed Oct 30 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-2
- Resolves: #1022834

* Fri Oct 18 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-1
- New upstream version 0.2.8 introducing cache_{check,dump,repair,restore}
  Resolves: #1020825

* Tue Sep 17 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.7-1
- New upstream version 0.2.7
  Resolves: #966264

* Wed Jul 31 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.3-1
- New upstream version

* Tue Jul 30 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.2-1
- New upstream version with missing man pages, thin_metadata_size
  calculator and thin_dump metadata snapshot support.
- Manual page header fixes

* Wed Jul 10 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.1-1
- New upstream version.

* Wed Jul 10 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.0-1
- New upstream version.

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Apr 19 2012 Milan Broz <mbroz@redhat.com> - 0.1.4-1
- Fix thin_check man page (add -q option).
- Install utilities in /usr/sbin.

* Tue Mar 13 2012 Milan Broz <mbroz@redhat.com> - 0.1.2-1
- New upstream version.

* Mon Mar 05 2012 Milan Broz <mbroz@redhat.com> - 0.1.1-1
- Fix quiet option.

* Fri Mar 02 2012 Milan Broz <mbroz@redhat.com> - 0.1.0-1
- New upstream version.

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.1-3
- Rebuilt for c++ ABI breakage

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Dec 21 2011 Milan Broz <mbroz@redhat.com> - 0.0.1-1
- Initial version
