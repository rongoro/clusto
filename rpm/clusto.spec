%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?py_version: %define py_version %(%{__python} -c "import sys; print sys.version[:3]")}

Name:		clusto
Version:	0.5.26
Release:	1%{?dist}
Summary:	Clusto is a cluster management tool

Group:		Utilities/System
License:	BSD
URL:		http://github.com/digg/clusto
Source0:	http://github.com/digg/clusto/tarball/%{name}-%{version}.tar.gz
Patch0:		clusto-0.5.26-patch0.patch
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	noarch
Packager:	Jorge A Gallegos <kad@blegh.net>

BuildRequires:	python-devel
BuildRequires:	python-sphinx-doc
%if 0%{?fedora} >= 8
BuildRequires:	python-setuptools-devel
%else
BuildRequires:	python-setuptools
%endif
Requires:	python-sqlalchemy >= 0.5
Requires:	ipython

%description
Clusto is a cluster management tool. It helps you keep track of your inventory,
where it is, how it's connected, and provides an abstracted interface for
interacting with the elements of the infrastructure.


%prep
%setup -q -n %{name}-%{version}
%patch0 -p1


%build
%{__python} -c 'import setuptools; execfile("setup.py")' build
# Build documentation
cd doc
make html


%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}
%{__python} -c 'import setuptools; execfile("setup.py")' install -O1 --skip-build --root %{buildroot}


%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc README LICENSE doc/.build/html
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}-%{version}-py%{py_version}.egg-info
%{_bindir}/*


%changelog
* Tue May 4 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-1
- First spec draft

