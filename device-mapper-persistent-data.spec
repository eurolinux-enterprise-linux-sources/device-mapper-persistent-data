#
# Copyright (C) 2011-2013 Red Hat, Inc
#
Summary: Device-mapper thin provisioning tools
Name: device-mapper-persistent-data
Version: 0.2.8
Release: 2%{?dist}
License: GPLv3+
Group: System Environment/Base
URL: https://github.com/jthornber/thin-provisioning-tools
Source0: https://github.com/jthornber/thin-provisioning-tools/archive/thin-provisioning-tools-v%{version}.tar.bz2
# Source1: https://github.com/jthornber/thin-provisioning-tools/archive/v%{version}.tar.gz
Patch0: device-mapper-persistent-data-0.2.8-1-missing-man-pages.patch
Patch1: device-mapper-persistent-data-0.2.8-1-missing-installs.patch
Patch2: device-mapper-persistent-data-0.2.8-1-fix_compile_errors.patch
BuildRequires: autoconf, expat-devel, libstdc++-devel, boost-devel
Requires: expat

%description
thin-provisioning-tools contains check,dump,restore,repair,rmap
and metadata_size tools to manage device-mapper thin provisioning
target metadata devices; cache check,dump,restore and repair tools
to manage device-mapper cache metadata devices are included.


%prep
%setup -q -n thin-provisioning-tools-%{version}
%patch0 -p1
%patch1 -p1
%patch2 -p1
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
%{_mandir}/man8/cache_restore.8.gz
%{_mandir}/man8/cache_repair.8.gz
%{_mandir}/man8/thin_check.8.gz
%{_mandir}/man8/thin_dump.8.gz
%{_mandir}/man8/thin_metadata_size.8.gz
%{_mandir}/man8/thin_repair.8.gz
%{_mandir}/man8/thin_restore.8.gz
%{_mandir}/man8/thin_rmap.8.gz
%{_sbindir}/cache_check
%{_sbindir}/cache_dump
%{_sbindir}/cache_restore
%{_sbindir}/cache_repair
%{_sbindir}/thin_check
%{_sbindir}/thin_dump
%{_sbindir}/thin_metadata_size
%{_sbindir}/thin_repair
%{_sbindir}/thin_restore
%{_sbindir}/thin_rmap

%changelog
* Mon Oct 21 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-2
- New upstream version 0.2.8 introducing cache_{check,dump,repair,restore}; missing patch
  Resolves: #1019217

* Fri Oct 18 2013 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.8-1
- New upstream version 0.2.8 introducing cache_{check,dump,repair,restore}
  Resolves: #1019217

* Wed Sep 17 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.7-1
- New upstream version 0.2.7
  Resolves: #1006059

* Mon Aug 12 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.6-1
- compile errors on RHEL-6.4 fixed
  Resolves: #814790

* Thu Aug 08 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.6-1
- New upstream version 0.2.6; working around build system providing
  old boost-devel-1.41.0-17.el6_4 with constraints
  Resolves: #814790

* Thu Aug 08 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.5-2
- New upstream version 0.2.5
- specfile fix
  Resolves: #814790

* Thu Aug 08 2012 Heinz Mauelshagen <heinzm@redhat.com> - 0.2.5-1
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
