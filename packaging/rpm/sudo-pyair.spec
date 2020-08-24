%define _rpmdir {{OUTPUT_DIR}}
%define buildroot {{BUILD_ROOT}}/BUILDROOT
%define _unpackaged_files_terminate_build 0

# Turn off python bytecompile automagic.
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')


Name:           sudo-pyair
Version:        {{VERSION}}
Release:        1%{?dist}
Summary:        4-eyes protocol for executing commands using sudo
License:        Propreitary

URL:            https://github.com/safiyat/sudo_pyair
Source0:        https://github.com/safiyat/sudo_pyair/archive/v{{VERSION}}.tar.gz
BuildArch:      noarch
Requires:       pam-python python python-requests python2-passlib rh-python36-python screen
BuildRoot:      {{BUILD_ROOT}}

%description
A tool that implements 4-eyes protocol when executing commands in a privileged environment.

%prep
# Prepare sources

%build
# Build the software

%install
mkdir -p %{buildroot}/usr/local/bin %{buildroot}/opt
install -m 0644 %{buildroot}/../SOURCES/{approver.py,python_pam_server.py} %{buildroot}/opt/
install -m 0755 %{buildroot}/../SOURCES/{approver,start_shared_screen} %{buildroot}/usr/local/bin/

%clean

%files
%defattr(-,root,root,-)
/usr/local/bin/approver
/usr/local/bin/start_shared_screen
/opt/approver.py
/opt/python_pam_server.py

%changelog
* Fri Aug 21 2020 Md Safiyat Reza <safiyat.reza@ericsson.com> {{VERSION}}-1
- Created sudo-pypair.

%pre

%post
##### Add a commented line to the file at /etc/pam.d/sudo
awk -i inplace '/^.*auth.*/{$0="#"$0;}1' /etc/pam.d/sudo

line="#auth       sufficient pam_python.so /opt/python_pam_server.py \
    debug=True approver_group= exempted_users="

# Prepend ${line} before the first occurence of `auth`.
sed -i -e "1,/^.*auth.*/ {/^.*auth.*/i\
    ${line}
    }" /etc/pam.d/sudo


##### Enable multi-user screen sharing feature.
chmod u+s $(which screen)
chmod 755 /var/run/screen

%preun


%postun
