Name:           deepin-liferaft
Version:        45.0.0
Release:        3%{?dist}
Summary:        Memory pressure dialog for Fedora systemd-oomd (Qt6/KF6 port)

License:        GPL-3.0-or-later
URL:            https://github.com/evernightvista/deepin-liferaft
Source0:        https://github.com/evernightvista/deepin-liferaft/releases/download/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  gettext
BuildRequires:  qt6-qtbase-devel
BuildRequires:  kf6-kcoreaddons-devel
BuildRequires:  kf6-ki18n-devel
BuildRequires:  systemd-devel
BuildRequires:  desktop-file-utils
BuildRequires:  fdupes

Requires:       qt6-qtbase
Requires:       kf6-kcoreaddons
Requires:       kf6-ki18n
Requires:       systemd
Requires:       hicolor-icon-theme

%description
deepin-liferaft is a GUI memory pressure dialog for Fedora systemd-oomd. It
watches PSI memory pressure and per-cgroup swap usage; when sustained pressure
is detected it pauses the top memory-consuming DDE application cgroups and shows
a dialog where the user can resume them or force-quit to free memory.

This package is the Qt6 / KDE Frameworks 6 port: it uses native Qt6 Widgets
and KF6::I18n for localization instead of DTK.  Translation catalogs are
shipped for de, fr, ja, ko, zh_CN and zh_TW.

%prep
%autosetup

%build
%cmake -DCMAKE_BUILD_TYPE=Release \
       -DCMAKE_INSTALL_PREFIX=%{_prefix} \
       -DLIB_INSTALL_DIR=%{_libdir} \
       -DSYSCONF_INSTALL_DIR=%{_sysconfdir} \
       -DSHARE_INSTALL_PREFIX=%{_datadir}
%cmake_build

%install
%cmake_install

# ki18n_install(po) (in CMakeLists) compiles and installs each catalog as
# %{buildroot}%{_datadir}/locale/<lang>/LC_MESSAGES/%{name}.mo when KF6 is
# present. As a fallback for build hosts without KF6 dev headers (e.g. a
# CI sandbox), compile the .po sources directly with msgfmt so %find_lang
# always has catalogs to package.
if [ ! -d %{buildroot}%{_datadir}/locale ]; then
    for po in po/*.po; do
        lang=$(basename "$po" .po)
        install -d -m 0755 %{buildroot}%{_datadir}/locale/"$lang"/LC_MESSAGES
        msgfmt -o %{buildroot}%{_datadir}/locale/"$lang"/LC_MESSAGES/%{name}.mo "$po"
    done
fi

# Validate desktop file and dedupe.
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop || :
%fdupes %{buildroot}%{_datadir}

%find_lang %{name} --with-qt --all-name

%check
%{buildroot}%{_bindir}/%{name} --self-test

%post
# Enable the user service globally so newly logged-in users auto-start it.
systemctl --global enable %{name}.service >/dev/null 2>&1 || :

%preun
if [ $1 -eq 0 ]; then
    # Disable the service on full uninstall only.
    systemctl --global disable %{name}.service >/dev/null 2>&1 || :
fi

%postun
systemctl --global daemon-reload >/dev/null 2>&1 || :

%files -f %{name}.lang
%doc README.md
%license LICENSE
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_userunitdir}/%{name}.service
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/%{name}/whitelist
%{_mandir}/man1/%{name}.1*

%changelog
* Mon Oct 12 2026 KairikiFedora <13278297951@sina.cn> - 45.0.0-3
- Rewrite spec for the Qt6/KF6 port: native Qt6 Widgets + KF6::I18n.
- Drop bundled SVG icon and resources.qrc; ship icon via hicolor theme.
- Add German, French and Traditional Chinese translation catalogs.
- Replace manual locale relocation hacks with %%find_lang.

* Wed Aug 26 2026 KairikiFedora <13278297951@sina.cn> - 45.0.0-2
- Remove bundled SVG icon and resources.qrc; load application icon from the
  system icon theme.

* Fri Aug 07 2026 KairikiFedora <13278297951@sina.cn> - 45.0.0-1
- Added support for Japanese, Korean, and Simplified Chinese translations.
- Added Verbose logging option for debugging.
- Enable systemd user service globally on installation.
