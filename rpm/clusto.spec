# Default variables
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?py_version: %define py_version %(%{__python} -c "import sys; print sys.version[:3]")}

# Defaults to --with-mysql unless --without mysql is specified, should this change?
%{!?_without_mysql: %{!?_with_mysql: %define _with_mysql --with-mysql}}
# Defaults to --without-psycopg2
%{!?_with_psycopg2: %{!?_without_psycopg2: %define _without_psycopg2 --without-psycopg2}}

Name:		clusto
Version:	0.5.26
Release:	4%{?dist}
Summary:	Tools and libraries for organizing and managing infrastructure

Group:		Applications/System
License:	BSD
URL:		http://github.com/digg/clusto
Source0:	http://github.com/digg/clusto/tarball/%{name}-%{version}.tar.gz
Patch0:		remove-github-ext-from-sphinx.patch
Patch1:		replace-var-with-libexec.patch
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	noarch

BuildRequires:	python-devel
BuildRequires:	python-sphinx-doc
%if 0%{?fedora} >= 8
BuildRequires:	python-setuptools-devel
%else
BuildRequires:	python-setuptools
%endif
Requires:	python-sqlalchemy >= 0.5
Requires:	ipython
Requires:	libvirt-python
Requires:   python-IPy
Requires:   scapy >= 2.0
%{?_with_mysql:Requires: MySQL-python}
%{?_with_psycopg2:Requires: python-psycopg2}

%description
Clusto is a cluster management tool. It helps you keep track of your inventory,
where it is, how it's connected, and provides an abstracted interface for
interacting with the elements of the infrastructure.


%prep
%setup -q -n %{name}-%{version}
%patch0 -p1
%patch1 -p1


%build
%{__python} -c 'import setuptools; execfile("setup.py")' build
# Build documentation
cd doc
make html
rm -f .build/html/.buildinfo


%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}
%{__python} -c 'import setuptools; execfile("setup.py")' install -O1 --skip-build --root %{buildroot}
# Create additional directories
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_libexecdir}/%{name}
cp conf/* %{buildroot}%{_sysconfdir}/%{name}/
cp contrib/* %{buildroot}%{_libexecdir}/%{name}/


%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc README LICENSE doc/.build/html
%config(noreplace) %{_sysconfdir}/%{name}
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}-%{version}-py%{py_version}.egg-info
%attr(0755, root, root) %{_libexecdir}/%{name}/*
%attr(0755, root, root) %{_bindir}/*


%changelog
* Wed May 5 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-4
- Adding python-IPy dependency

* Wed May 5 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-3
- Packager should go in ~/.rpmmacros

* Tue May 4 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-2
- Moved contrib from /var/lib/clusto to /usr/libexec/clusto
- Added sysconf directory defaults
- Added scapy dependency
- Added libvirt-python dependency
- Added mysql conditional dependency (defaults to --with)
- Added psycopg2 conditional dependency (defaults to --without)

* Tue May 4 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-1
- First spec draft

