# Memory Liferaft

<p align="center">
  <img src="data/icons/deepin-liferaft.svg" width="128" alt="Memory Liferaft icon">
</p>

Memory Liferaft (`deepin-liferaft`, Chinese 内存救生筏) is a single-binary
**Qt6 / KDE Frameworks 6** application that shows an out-of-memory dialog when
sustained memory pressure is detected. It pauses application cgroups before the
desktop becomes unusable, and lets the user resume or force-quit an
application. The UI uses native Qt6 Widgets and follows the system theme
(light/dark and accent color) without any Deepin-specific toolkit.

It was originally a DTK 6 application for Deepin; this port replaces the DTK
widget set with plain Qt6 Widgets and the DTK translation system with KDE
Framework 6's `KF6::I18n`. The cgroup / PSI / systemd integration is
unchanged.

The monitor now recognizes **both** Deepin and KDE Plasma sessions: it scans
DDE launch groups (`app-DDE-*`), KDE/systemd transient app units
(`app-<id>@<rand>.service`, e.g. `app-plasmashell@…`), and self-managed scopes
(`app-<id>-<pid>.scope`). The packaged whitelist protects the DDE desktop
shell (`dde-shell`, `dde-lock`) **and** the KDE Plasma desktop core
(`plasmashell` panel/taskbar, `kscreenlocker_greet` lock screen, `ksmserver`,
`kwin_x11` / `kwin_wayland`, `kglobalaccel`, `kded6`), so neither desktop's
taskbar or lock screen can be frozen or killed by the dialog.

## Behavior

- Polls the current `user@UID.service` cgroup every second.
- Uses Fedora's workstation systemd-oomd policy: `full avg10` above 50% for
  20 seconds, with reclaim activity (`pgscan`) seen in the last 30 seconds.
- Also triggers when system memory and swap usage both exceed 90% and an
  application uses more than 5% of total swap.
- Lists up to 10 application cgroups by `memory.current`, recognizing DDE
  launch groups (`app-DDE-*`), KDE/systemd transient units
  (`app-<id>@<rand>.service`), and self-managed scopes
  (`app-<id>-<pid>.scope`).
- Attributes child resources to the application cgroup. A `memhog` process
  launched in Deepin Terminal therefore increases the Terminal row.
- Reads localized names and icons from XDG desktop files, including the
  Linglong export directory at
  `/var/lib/linglong/entries/apps/share/applications`.
- Ranks pressure candidates by the latest `pgscan` delta and then memory, or
  ranks swap candidates by `memory.swap.current`.
- Freezes up to three candidates with `cgroup.freeze`; Resume thaws the
  selected group and Force Quit uses `cgroup.kill`.
- Asks for confirmation when the window is closed while applications are
  still paused, and only resumes them once the close is confirmed. Cancelling
  keeps the window and the paused applications as they are.
- Waits 15 seconds after an action before showing another dialog.

Detection follows Fedora's systemd-oomd policy while the presentation follows
the Deepin design language. systemd-oomd kills one cgroup immediately;
Memory Liferaft pauses up to three candidates and leaves the final choice to
the user.

## Dialog

The window is a `QMainWindow` with a standard Qt titlebar. Its content
mirrors the DDE style using plain Qt6 Widgets:

- A rounded alert banner with a warning badge, a title, a short explanation,
  and the machine's total and available memory plus its swap. The numbers
  follow the same one-second sample as the trigger policy, so they show what
  the pressure decision sees; a board without swap says so, and an unreadable
  `/proc/meminfo` shows no numbers at all.
- A `QListView` of applications with alternating row shading (even rows use
  `QPalette::AlternateBase`, odd rows `QPalette::Base`), an accent-colored
  selection, and a hover highlight, drawn by a custom `QStyledItemDelegate`.
  Under `Application` and `Memory` column captions, each row shows the
  application icon, its localized name, a `Paused` tag when the cgroup is
  frozen, and right-aligned memory usage.
- A separator above a right-aligned button row: `Resume` for the selected
  frozen application and `Force Quit`, styled as a destructive button.
- A `QDialog` confirmation before the window closes while applications are
  still paused, since closing resumes them. `Cancel` is the default button,
  so a stray Enter or Escape keeps the paused applications paused.
- Colors come from `QPalette`, so the dialog follows light and dark themes
  and the system accent color without hard-coded values.

## Translations

User-visible strings are wrapped with the `L()` macro, which expands to KF6
`i18n()` when `HAVE_KF6` is defined and to `QObject::tr()` otherwise. Source
catalogs are gettext `.po` files in `po/`:

| File     | Language             |
| -------- | -------------------- |
| `de.po`  | German               |
| `fr.po`  | French               |
| `ja.po`  | Japanese             |
| `ko.po`  | Korean               |
| `zh_CN.po` | Simplified Chinese |
| `zh_TW.po` | Traditional Chinese |

`po/deepin-liferaft.pot` is the template regenerated with:

```bash
xgettext --package-name=deepin-liferaft --package-version=45.0.0 \
         --msgid-bugs-address=ston.jia@outlook.com \
         --keyword=L --keyword=i18n -o po/deepin-liferaft.pot \
         -C --from-code=UTF-8 --no-location main.cpp
```

After adding or changing strings, update each catalog with:

```bash
msgmerge --update --no-location po/<lang>.po po/deepin-liferaft.pot
```

CMake compiles the catalogs to `.mo` via KF6's `ki18n_install(po)` and
installs them to `/usr/share/locale/<lang>/LC_MESSAGES/deepin-liferaft.mo`.
`KLocalizedString::setupCatalogDomain()` (called from `main.cpp`) binds the
`deepin-liferaft` domain so KF6 picks the right catalog at runtime.

## Whitelist

Whitelisted applications never appear in the dialog's application list and
are never frozen or force quit. Entries are desktop file IDs, the same IDs
parsed from cgroup unit names — for example `google-chrome` matches
`app-DDE-google\x2dchrome@....service`. Write one ID per line; blank lines
and `#` comments are ignored.

Following the vim configuration model, three levels are merged into one set:

| Level | File |
| --- | --- |
| Package defaults | `/usr/share/deepin-liferaft/whitelist` |
| System administrator | `/etc/deepin-liferaft/whitelist` |
| Per-user | `~/.config/deepin-liferaft/whitelist` |

The packaged defaults protect the monitor itself, the DDE screen locker
(`dde-lock`) and desktop shell (`dde-shell`), and the KDE Plasma desktop core:
`plasmashell` (panel / taskbar), `kscreenlocker_greet` (lock-screen greeter),
`ksmserver` (session manager, also drives the screen locker), `kwin_x11` /
`kwin_wayland` (window manager), `kglobalaccel` (global shortcuts), and
`kded6` (KF6 background daemon). These are matched by desktop file ID parsed
from the cgroup unit name, so KDE sessions started through systemd transient
units (`app-<id>@<rand>.service`) are recognized the same way DDE launch
groups are. The whitelist is loaded once at startup, so restart the service
after editing:

```bash
systemctl --user restart deepin-liferaft.service
```

The startup log records how many entries were loaded.

## Safety

Memory Liferaft only thaws cgroups it froze itself. It skips cgroups already
frozen by another component and never freezes the cgroup containing its own
process.

Closing the dialog thaws every owned cgroup before the window closes. If a
thaw temporarily fails, the window remains open and retries. `SIGTERM` and
`SIGINT`, including `systemctl --user stop`, are received through `signalfd`
so owned cgroups are thawed before process exit.

Invalid PSI, `memory.stat`, `memory.current`, or `/proc/meminfo` samples do
not trigger an action.

The systemd user service sets `MemoryMin=16M`, which gives the monitor's own
cgroup hard reclaim protection: the kernel will not swap out or reclaim its
protected pages even under extreme memory pressure, so the daemon can keep
polling PSI and raise the dialog exactly when the rest of the system is
starving. 16 MiB covers the measured hidden-mode working set (about 13 MiB
PSS) with margin. cgroup v2 caps a leaf cgroup's effective protection by its
ancestors' `memory.min`; Deepin sessions already protect the whole
`user.slice` chain, so the leaf protection is effective there. This
protection applies to service mode and requires systemd 253 or newer (older
versions ignore the unknown property); manual foreground runs from a
terminal have no such protection.

## Logging

Memory Liferaft logs through Qt's logging categories (`qInfo` / `qWarning`).
Under the systemd user service messages go to the user journal; run from a
terminal, they also appear on stderr.

Inspect the daemon's status:

```bash
journalctl --user -u deepin-liferaft.service -f
```

The journal records program startup (pid and hidden/foreground mode),
pressure threshold crossings, trigger decisions with pressure, duration,
reclaim and memory usage, every freeze (cgroup, trigger, sort metric), every
force quit (kill/thaw result), resume and thaw failures, and shutdown
cleanup. Invalid samples are logged as warnings on state change rather than
every second.

The service unit overrides the DDE session default `QT_LOGGING_RULES` (which
suppresses `qInfo` in journald) so that Info-level messages reach the
journal:

```bash
systemctl --user daemon-reload
systemctl --user restart deepin-liferaft.service
```

## Resource Use

`--hidden` mode delays creation of the list, labels, buttons, and
icon-theme data until the dialog is first shown. It also avoids scanning
every application cgroup while pressure is low and the window is hidden.

On the development machine, measured three seconds after startup:

| Metric | Before | After |
| --- | ---: | ---: |
| RSS | 60.7 MiB | 52.7 MiB |
| PSS | 19.4 MiB | 13.0 MiB |
| Private dirty | 9.85 MiB | 7.93 MiB |

Most remaining RSS is shared Qt6 / KF6 code. An otherwise empty Qt6
`QApplication` measured about 38 MiB RSS on the same machine, so RSS alone
overstates private memory cost.

## Requirements

- Linux cgroup v2 with `memory`, `memory.swap`, `memory.pressure`,
  `cgroup.freeze`, and `cgroup.kill`
- Deepin sessions that place applications in `app-DDE-*` cgroups
- Qt 6 Widgets development packages
- KDE Frameworks 6 `ki18n` development package (`kf6-ki18n-devel` on Fedora)
- GNU gettext for regenerating `.po` catalogs
- CMake 3.16 or newer and a C++17 compiler

## Kernel PSI

deepin-liferaft reads `memory.pressure`, which requires kernel PSI. Some
Deepin kernels build with `CONFIG_PSI_DEFAULT_DISABLED=y`, so PSI is off
until the `psi=1` kernel parameter is passed at boot.

This Qt6/KF6 port no longer ships a GRUB snippet (the `data/grub/` directory
has been removed from the source tree). Enable PSI manually by appending
`psi=1` to your bootloader's kernel command line and rebooting.

For GRUB-based systems, add `psi=1` to `GRUB_CMDLINE_LINUX_DEFAULT` in
`/etc/default/grub` and run:

```bash
sudo update-grub
```

For systemd-boot, append `psi=1` to the kernel options in your loader
entry. For other bootloaders, consult the relevant documentation.

PSI cannot be enabled at runtime on a `CONFIG_PSI_DEFAULT_DISABLED=y`
kernel; a reboot is required.

## Build and Test

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

The self-test covers PSI parsing, pressure and swap threshold boundaries,
`pgscan` sampling failures, memory formatting, freezer ownership/thaw
behavior, and whitelist parsing, merging, and application filtering.

Run visibly for UI inspection:

```bash
./build/deepin-liferaft
```

Run as a hidden monitor:

```bash
./build/deepin-liferaft --hidden
```

## RPM Package (Fedora)

```bash
sudo dnf install rpmdevtools
spectool -g -R deepin-liferaft.spec
rpmbuild -ba deepin-liferaft.spec
sudo dnf install ~/rpmbuild/RPMS/$(uname -m)/deepin-liferaft-45.0.0-3.*.rpm
```

The package installs:

- `/usr/bin/deepin-liferaft`
- `/usr/lib/systemd/user/deepin-liferaft.service`
- `/usr/share/applications/deepin-liferaft.desktop`
- `/usr/share/icons/hicolor/scalable/apps/deepin-liferaft.svg`
- `/usr/share/man/man1/deepin-liferaft.1.gz`
- `/usr/share/deepin-liferaft/whitelist` with the packaged whitelist defaults
- `/usr/share/locale/<lang>/LC_MESSAGES/deepin-liferaft.mo` for `de`, `fr`,
  `ja`, `ko`, `zh_CN`, and `zh_TW`

The spec uses the standard `%find_lang` macro to package translation
catalogs, so adding a new language only requires dropping its `<lang>.po`
file into `po/`.

## User Service

The service starts the monitor with `--hidden` in graphical sessions. The
RPM `%post` script enables the user unit globally, so a per-user `disable`
does not override the global enable link.

Disable only for the current user:

```bash
systemctl --user mask --now deepin-liferaft.service
```

Restore it:

```bash
systemctl --user unmask deepin-liferaft.service
systemctl --user enable --now deepin-liferaft.service
```

Disable global enable for all users, then stop the current session instance:

```bash
sudo systemctl --global disable deepin-liferaft.service
systemctl --user stop deepin-liferaft.service
```

Inspect status:

```bash
systemctl --user status deepin-liferaft.service
```

## Platform Differences

Linux PSI and systemd cgroups replace macOS VM-pressure and application
lifecycle APIs. The interaction is modelled on the macOS "out of application
memory" alert, but DDE cgroups define application boundaries, Fedora's
systemd-oomd thresholds decide when to show the dialog, and Qt6 Widgets plus
KF6 I18n supply native styling and localization.

## License

Memory Liferaft is licensed under [GPL-3.0-or-later](LICENSE).
