#
# Copyright (C) 2011-2016 Red Hat, Inc
#

%define pre_release_upstream -rc7
%define pre_release rc7

Summary: Device-mapper Persistent Data Tools
Name: device-mapper-persistent-data
Version: 0.6.2
Release: 0.2.%{pre_release}%{?dist}
License: GPLv3+
Group: System Environment/Base
URL: https://github.com/jthornber/thin-provisioning-tools
Source0: https://github.com/jthornber/thin-provisioning-tools/archive/thin-provisioning-tools-%{version}%{pre_release_upstream}.tar.gz
Patch0: device-mapper-persistent-data-document-clear-needs-check-flag.patch
Patch1: device-mapper-persistent-data-add-era_restore-and-cache_metadata_size-man-pages.patch
Patch2: device-mapper-persistent-data-avoid-strip.patch
Patch3: device-mapper-persistent-data-use-exec-prefix-for-sbin.patch
Patch4: device-mapper-persistent-data-update-thin_dump-manpage.patch

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
%setup -q -n thin-provisioning-tools-%{version}%{pre_release_upstream}
%patch0 -p1 -b .clear_needs_check_flag
%patch1 -p1 -b .man_pages
%patch2 -p1 -b .avoid_strip
%patch3 -p1 -b .exec_prefix
%patch4 -p1 -b .thin_dump_man

echo %{version}-%{release} > VERSION

%build
%define _sbindir /sbin
%define _usrsbindir /usr/sbin
autoconf
%configure --enable-static-cxx --with-optimisation= --exec_prefix=/
make %{?_smp_mflags} V=

%install
make DESTDIR=%{buildroot} MANDIR=%{_mandir} install
# The pdata_tools with symlinks for tools are in /sbin
# Also create symlinks in /usr/sbin for compatibility.
mkdir %{buildroot}%{_usrsbindir}
for tool_path in %{buildroot}%{_sbindir}/* ; do
	tool=$(basename ${tool_path})
	ln -s ../..%{_sbindir}/${tool} %{buildroot}%{_usrsbindir}/${tool}
done

%clean

%files
%doc COPYING README.md
%{_mandir}/man8/cache_check.8.gz
%{_mandir}/man8/cache_dump.8.gz
%{_mandir}/man8/cache_restore.8.gz
%{_mandir}/man8/cache_repair.8.gz
%{_mandir}/man8/era_check.8.gz
%{_mandir}/man8/era_dump.8.gz
%{_mandir}/man8/era_invalidate.8.gz
%{_mandir}/man8/thin_check.8.gz
%{_mandir}/man8/thin_delta.8.gz
%{_mandir}/man8/thin_dump.8.gz
%{_mandir}/man8/thin_ls.8.gz
%{_mandir}/man8/thin_metadata_size.8.gz
%{_mandir}/man8/thin_restore.8.gz
%{_mandir}/man8/thin_repair.8.gz
%{_mandir}/man8/thin_rmap.8.gz
%{_mandir}/man8/thin_trim.8.gz
%{_sbindir}/pdata_tools
%{_usrsbindir}/pdata_tools
%{_sbindir}/cache_check
%{_usrsbindir}/cache_check
%{_sbindir}/cache_dump
%{_usrsbindir}/cache_dump
%{_sbindir}/cache_metadata_size
%{_usrsbindir}/cache_metadata_size
%{_sbindir}/cache_restore
%{_usrsbindir}/cache_restore
%{_sbindir}/cache_repair
%{_usrsbindir}/cache_repair
%{_sbindir}/era_check
%{_usrsbindir}/era_check
%{_sbindir}/era_dump
%{_usrsbindir}/era_dump
%{_sbindir}/era_restore
%{_usrsbindir}/era_restore
%{_sbindir}/era_invalidate
%{_usrsbindir}/era_invalidate
%{_sbindir}/thin_check
%{_usrsbindir}/thin_check
%{_sbindir}/thin_delta
%{_usrsbindir}/thin_delta
%{_sbindir}/thin_dump
%{_usrsbindir}/thin_dump
%{_sbindir}/thin_ls
%{_usrsbindir}/thin_ls
%{_sbindir}/thin_metadata_size
%{_usrsbindir}/thin_metadata_size
%{_sbindir}/thin_restore
%{_usrsbindir}/thin_restore
%{_sbindir}/thin_repair
%{_usrsbindir}/thin_repair
%{_sbindir}/thin_rmap
%{_usrsbindir}/thin_rmap
%{_sbindir}/thin_trim
%{_usrsbindir}/thin_trim

%changelog
* Tue Feb 20 2018 Marian Csontos <mcsontos@redhat.com> - 0.6.2-0.2.rc7
- Fix usage of --metadata-snap in thin_dump manpage.

* Tue Mar 22 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-0.1.rc7
- Fixes for thin_repair.
- Add new fields to thin_ls: MAPPED_BYTES, EXCLUSIVE_BYTES and SHARED_BYTES.

* Wed Feb 24 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-0.1.rc5
- Fix bugs in thin_delta.
- Fix recent regression in thin_repair.
- Force g++-98 dialect.

* Wed Feb 10 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.2-0.1.rc1
- Fix bug in thin_dump when using metadata snaps.

* Wed Feb 10 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.1-1
- Install pdata_tools and all its symlinks for various tools to
  /sbin and also provide symlinks for all tools in /usr/sbin
  for backward compatibility.
- Link with libstdc++ statically.

* Thu Jan 21 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.0-2
- Add proper cmath header file to sources.

* Wed Jan 20 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.6.0-1
- New thin_ls command.

* Wed Jan 20 2016 Peter Rajnoha <prajnoha@redhat.com> - 0.5.6-1
- era_invalidate may be run on live metadata if the --metadata-snap
  option is given.
- Update man pages to make it clearer that most tools shouldn't
  be run on live metadata.
- Fixed bugs in the metadata reference counting for thin_check.
- New thin_delta and thin_trim commands.
- New --clear-needs-check option for cache_check.
- Space map checking for thin check.
- All tools switch to using libaio. This gives a large performance
  boost, especially to the write focused tools like thin_restore.
- Added progress monitor to thin_restore, cache_restore and era_restore.
- Added --quiet/-q option to *_restore to turn off the progress bar.
- Removed variable hint size support from cache tools.
- Tools are now rolled into a single executable to save space.
- Fixed bugs when walking bitsets (possibly effecting cache_dump
  and cache_check).

* Thu Apr 3 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.3.2-1
- New upstream version 0.3.2 introducing era_{check,dump,invalidate}
  Resolves: #1035990 #1084081

* Thu Jan 30 2014 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-3
  Resolves: #1035990

* Mon Oct 21 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-2
- New upstream version 0.2.8 introducing cache_{check,dump,repair,restore}; missing patch
  Resolves: #1019217

* Fri Oct 18 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-1
- New upstream version 0.2.8 introducing cache_{check,dump,repair,restore}
  Resolves: #1019217

* Mon Sep 17 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.7-1
- New upstream version 0.2.7
  Resolves: #1006059

* Sun Aug 12 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.6-1
- compile errors on RHEL-6.4 fixed
  Resolves: #814790

* Wed Aug 08 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.6-1
- New upstream version 0.2.6; working around build system providing
  old boost-devel-1.41.0-17.el6_4 with constraints
  Resolves: #814790

* Wed Aug 08 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.5-2
- New upstream version 0.2.5
- specfile fix
  Resolves: #814790

* Wed Aug 08 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.5-1
- New upstream version 0.2.5
  Resolves: #814790

* Thu Mar 15 2012 Milan Broz <mbroz@redhat.com> - 0.1.4-1
- Fix thin_check man page (add -q option).
- Install utilities in /usr/sbin.
  Resolves: #803204 #803144

* Tue Mar 13 2012 Milan Broz <mbroz@redhat.com> - 0.1.2-1
- New upstream version.
  Resolves: #802242 #802244

* Fri Mar 02 2012 Milan Broz <mbroz@redhat.com> - 0.1.0-1
- New upstream version.
  Resolves: #796114 #760614

* Wed Dec 21 2011 Milan Broz <mbroz@redhat.com> - 0.0.1-1
- Initial version
