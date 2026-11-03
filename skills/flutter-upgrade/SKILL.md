---
name: flutter-upgrade
description: Flutter upgrade workflow. Use when upgrading Flutter SDK, bumping Flutter version, migrating to a new Flutter release, or resolving breaking changes after a Flutter update.
argument-hint: <target version>
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Flutter Upgrade Workflow

Upgrade Flutter SDK and all dependencies to the version specified in $ARGUMENTS (or the latest stable if not specified).

## Usage

```
/flutter-upgrade 3.24
/flutter-upgrade 3.22.3
/flutter-upgrade          # upgrades to latest stable
```

## Gotchas
- `dart fix --apply` (Step 6) runs AFTER quality gates (Step 5). If it changes code, quality gates need re-running — but no re-run step exists in the workflow. Re-run them manually.
- `flutter pub upgrade --major-versions` upgrades all packages at once. If multiple break simultaneously, isolating the cause is very difficult. Consider upgrading high-risk packages individually.

## Instructions

1. **Pre-upgrade checks:**
   - Run `flutter pub outdated` to see what will be upgraded
   - Determine current Flutter version with `flutter --version`
   - Determine target version: $ARGUMENTS if provided, else look up latest stable on https://docs.flutter.dev/release/archive
   - Enumerate every stable release between current and target (e.g. 3.32 → 3.44 means 3.33, 3.34, … 3.44). For each one, fetch its entry on https://docs.flutter.dev/release/breaking-changes and its release notes / "What's new" post linked from https://docs.flutter.dev/release/release-notes. Collect every breaking change, deprecation, and required migration that touches this project (check Android/iOS/web/desktop sections based on what the app targets). Do this dynamically — don't rely on a hardcoded list, since this skill won't be updated for every release.
   - Summarize the collected breaking changes back to the user before proceeding, and note any that require manual code changes vs. those handled by `dart fix --apply` or CLI auto-migration.
   - Ensure git working tree is clean (`git status`)

2. **Upgrade Flutter SDK:**
   ```bash
   # To latest stable:
   flutter upgrade

   # To a specific version:
   flutter downgrade $ARGUMENTS  # if pinning to older
   # or switch channel and upgrade as needed
   ```

3. **Upgrade dependencies:**
   ```bash
   flutter pub upgrade --major-versions
   ```

4. **Regenerate code** (if using code generation):
   ```bash
   make generate  # or: dart run build_runner build --delete-conflicting-outputs
   ```

5. **Run quality gates:**
   ```bash
   flutter analyze
   dart run custom_lint  # if using Riverpod/custom linters
   make test  # or: flutter test
   ```

6. **Apply automated fixes** (if analyzer suggests migrations):
   ```bash
   dart fix --apply
   ```

7. **Manual testing:**
   - Run on iOS simulator and Android emulator (or physical devices)
   - Test navigation flows (push, pop, deep links)
   - Test platform-specific features (camera, permissions, notifications)
   - Test areas affected by major version upgrades (check changelogs)
   - Verify release/profile builds, not just debug

8. **Document changes:**
   - List all packages that changed versions and why
   - Note any code modifications required by breaking changes
   - Record any deprecation warnings that remain (with plan to address)

## Examples

**Routine upgrade:**
> /flutter-upgrade

Runs `flutter upgrade` to latest stable, `flutter pub upgrade --major-versions`, regenerates code, runs analyze + tests. Reports any breaking changes found.

**Targeted version upgrade:**
> /flutter-upgrade 3.24

Upgrades to Flutter 3.24 specifically. Checks the release notes at https://docs.flutter.dev/release/release-notes for 3.24, identifies breaking changes, upgrades SDK and dependencies, runs full quality gates.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `flutter pub upgrade` version conflicts | Run `flutter pub outdated` to identify the conflict. Try upgrading the blocking package first, or add a dependency override temporarily. |
| `build_runner` fails after upgrade | Delete `.dart_tool/` and `build/` directories, then re-run. Check that `build_runner` version is compatible with new SDK. |
| `flutter analyze` shows new deprecations | Run `dart fix --apply` for auto-fixable issues. For manual fixes, check the deprecation message for the replacement API. |
| iOS build fails after SDK upgrade | Run `cd ios && pod repo update && pod install`. If still failing, delete `Podfile.lock` and `Pods/`, then retry. |
| Android build fails with Gradle errors | Check `android/gradle/wrapper/gradle-wrapper.properties` matches the required Gradle version for the new Flutter SDK. Run `cd android && ./gradlew clean`. |
| Platform channel errors at runtime | Rebuild from clean: `flutter clean && flutter pub get`. Platform channel APIs may have changed — check the plugin's changelog. |

## Guidelines

- For major version upgrades, always check package changelogs for breaking changes
- Search for migration guides: `[package-name] [old-version] to [new-version] migration`
- Upgrade incrementally when jumping multiple major versions
- Test thoroughly on both platforms before considering upgrade complete
- Clear caches after upgrade: `flutter clean && flutter pub get`
