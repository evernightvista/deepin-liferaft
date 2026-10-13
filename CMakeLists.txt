cmake_minimum_required(VERSION 3.16)
project(deepin-liferaft CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_AUTOMOC ON)

# Version is defined here; the binary embeds it via LIFERAFT_VERSION.
set(LIFERAFT_VERSION "45.0.0")

# Minimum versions for Qt6 and KDE Frameworks 6.
set(QT_MIN_VERSION "6.4.0")
set(KF6_MIN_VERSION "6.0.0")

find_package(Qt6 ${QT_MIN_VERSION} NO_MODULE COMPONENTS Widgets REQUIRED)

# KF6 I18n: use the standalone KF6I18n config that kf6-ki18n-devel ships at
# /usr/lib64/cmake/KF6I18n. The previous `find_package(KF6 COMPONENTS I18n)`
# relies on a top-level umbrella KF6Config that is not present when only
# kf6-ki18n-devel (and a few other framework -devel packages) are installed;
# that find fails silently, `KF6::I18n` is never defined, HAVE_KF6 stays
# unset, and the binary falls back to QObject::tr() with no QTranslator, so
# every string renders in English.
find_package(KF6I18n ${KF6_MIN_VERSION} REQUIRED)

add_executable(deepin-liferaft main.cpp)

target_link_libraries(deepin-liferaft PRIVATE Qt6::Widgets KF6::I18n)
target_compile_definitions(deepin-liferaft PRIVATE
    LIFERAFT_VERSION="${LIFERAFT_VERSION}"
    HAVE_KF6)

# Translations.
# KF6's ki18n_install(po) expects the KDE sub-directory layout po/<lang>/<domain>.po
# and derives both the language directory and the catalog file name from the path.
# This tree ships the flat layout po/<lang>.po, under which ki18n_install would
# (wrongly) emit share/locale/LC_MESSAGES/<lang>.mo: the catalog name would be the
# language code instead of the application domain, so gettext would never find
# deepin-liferaft.mo and every string would fall back to English. Compile the
# catalogs explicitly so each po/<lang>.po becomes
# share/locale/<lang>/LC_MESSAGES/deepin-liferaft.mo — exactly what
# KLocalizedString::setApplicationDomain("deepin-liferaft") loads at runtime.
find_package(Gettext REQUIRED)
file(GLOB LIFERAFT_PO_FILES CONFIGURE_DEPENDS "${CMAKE_SOURCE_DIR}/po/*.po")
set(LIFERAFT_MO_FILES "")
foreach(po_file IN LISTS LIFERAFT_PO_FILES)
    get_filename_component(lang "${po_file}" NAME_WE)
    set(mo_file "${CMAKE_CURRENT_BINARY_DIR}/locale/${lang}/LC_MESSAGES/deepin-liferaft.mo")
    add_custom_command(
        OUTPUT "${mo_file}"
        COMMAND "${GETTEXT_MSGFMT_EXECUTABLE}" -o "${mo_file}" "${po_file}"
        DEPENDS "${po_file}"
        VERBATIM)
    list(APPEND LIFERAFT_MO_FILES "${mo_file}")
    install(FILES "${mo_file}"
            DESTINATION "share/locale/${lang}/LC_MESSAGES")
endforeach()
if(LIFERAFT_MO_FILES)
    add_custom_target(translations ALL DEPENDS ${LIFERAFT_MO_FILES})
    add_dependencies(deepin-liferaft translations)
endif()

enable_testing()
add_test(NAME self-test COMMAND deepin-liferaft --self-test)

install(TARGETS deepin-liferaft RUNTIME DESTINATION bin)
install(FILES deepin-liferaft.service DESTINATION lib/systemd/user)
install(FILES deepin-liferaft.desktop DESTINATION share/applications)
install(FILES data/icons/deepin-liferaft.svg DESTINATION share/icons/hicolor/scalable/apps)
install(FILES data/whitelist DESTINATION share/deepin-liferaft)
install(FILES deepin-liferaft.1 DESTINATION share/man/man1)
install(FILES README.md DESTINATION share/doc/deepin-liferaft)
