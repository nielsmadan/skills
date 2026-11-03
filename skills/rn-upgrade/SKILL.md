---
name: rn-upgrade
description: React Native upgrade workflow. Use when upgrading React Native, bumping RN version, migrating to a new RN release, or resolving breaking changes after a React Native update.
argument-hint: <target version>
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# React Native Upgrade Command

You are tasked with upgrading a React Native application to the version specified in $ARGUMENTS (or the latest version if not specified).

## Usage

```
/rn-upgrade 0.76
/rn-upgrade 0.75.4
/rn-upgrade          # upgrades to latest stable
```

## Gotchas
- The rn-diff-purge diff reflects a pristine RN template only. Custom native code (modified `MainApplication.kt`, `AppDelegate.swift`) may be silently overwritten because it's not in the diff.
- Multi-version jumps (e.g., 0.73 → 0.76) require building and testing at each intermediate version. A breakage at 0.74 that is masked until 0.76 is much harder to diagnose.

## Instructions

1. **Determine versions:**
   - Check the current React Native version in package.json
   - If $ARGUMENTS is not specified, fetch the latest stable version from https://github.com/facebook/react-native/releases
   - Record: current version = X, target version = Y

2. **Research and validate:**
   - Fetch the release notes for the target version from https://github.com/facebook/react-native/releases/tag/v{target}
   - Use `research-tech` if release notes mention major changes (e.g., New Architecture default, Kotlin/Swift migration)
   - List any breaking changes that affect this project

3. **Fetch the upgrade diff:**
   - Construct the diff URL: `https://raw.githubusercontent.com/react-native-community/rn-diff-purge/diffs/diffs/{current}..{target}.diff`
   - Fetch and analyze the diff to understand all required changes
   - If the diff is unavailable, fall back to the Upgrade Helper UI: https://react-native-community.github.io/upgrade-helper/?from={current}&to={target}

4. **Check dependency compatibility:**
   - List all third-party native modules from package.json
   - For each critical dependency, check its GitHub repo releases/changelog for target RN version support:
     - Firebase: https://github.com/invertase/react-native-firebase/releases
     - Navigation: https://github.com/react-navigation/react-navigation/releases
     - Reanimated: https://github.com/software-mansion/react-native-reanimated/releases
     - Gesture Handler: https://github.com/software-mansion/react-native-gesture-handler/releases
     - Custom native modules in the project
   - Flag any library that hasn't released a compatible version yet and recommend: pin, fork, or find alternative

5. **Plan the upgrade:**
   - Create a task list with TaskCreate, broken into phases:
     - Phase 1: Dependency updates (package.json)
     - Phase 2: Android native changes (MainApplication, Gradle, gradle.properties)
     - Phase 3: iOS native changes (AppDelegate, Podfile, Info.plist, .pbxproj)
     - Phase 4: Library-specific migrations
     - Phase 5: Install dependencies and pods
   - Use EnterPlanMode to present the plan to the user for approval before making changes

6. **Execute the upgrade:**
   - Update package.json with new React Native and React versions
   - Update all @react-native/* packages to match the target version
   - Apply native code changes from the diff, preserving:
     - Custom package names/bundle identifiers
     - Third-party SDK integrations (e.g., Firebase, analytics, crash reporting)
     - Custom build configurations
     - Existing native modules
   - Update Gradle wrapper if required by the diff
   - Enable/configure New Architecture if required
   - Install dependencies: `yarn install` (or `npm install`)
   - Install iOS pods: `cd ios && pod install`

7. **Important considerations:**
   - ALWAYS preserve custom native code integrations
   - Replace template package names (e.g., com.helloworld) with the project's actual package names
   - Check for react-native-fast-image compatibility (may need @d11/react-native-fast-image fork)
   - Update related dependencies if needed (e.g., react-native-bootsplash, react-native-safe-area-context)
   - Never skip steps without user confirmation

8. **Post-upgrade checklist:**
   - Provide a testing checklist including:
     - Clean builds for both platforms (`cd android && ./gradlew clean`, Xcode clean build folder)
     - New Architecture verification (if enabled)
     - Third-party integrations testing
     - Navigation and animations
     - Device-specific features (camera, location, notifications, etc.)

9. **Documentation:**
   - Summarize all changes made
   - List any manual follow-up actions required
   - Note any dependencies that still need updates
   - Provide links to relevant release notes

## Examples

**Single version upgrade:**
> /rn-upgrade 0.76

Upgrades from current version (e.g., 0.75.3) to 0.76. Fetches the diff from rn-diff-purge, checks dependency compatibility, plans changes, and executes after approval.

**Multi-version jump:**
> /rn-upgrade 0.76

When current version is 0.73 or older, the skill upgrades incrementally: 0.73 -> 0.74 -> 0.75 -> 0.76, one major version at a time, validating builds between each jump.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pod install` fails with version conflicts | Run `cd ios && pod repo update && pod install`. If still failing, delete `Podfile.lock` and `Pods/` then retry. |
| Gradle build fails after upgrade | Clear caches: `cd android && ./gradlew clean`. Check that `gradle-wrapper.properties` matches the version from the diff. |
| Metro bundler can't resolve modules | Clear Metro cache: `npx react-native start --reset-cache`. Also delete `node_modules` and reinstall. |
| Xcode build fails with "framework not found" | Run `cd ios && pod deintegrate && pod install`. If using use_frameworks!, check compatibility with native modules. |
| New Architecture bridge errors | Verify all native modules support the New Architecture. Check `newArchEnabled` in `gradle.properties` (Android) and Podfile flags (iOS). |
| Diff URL returns 404 | The exact patch version may not exist in rn-diff-purge. Use the nearest available version or the Upgrade Helper UI. |

## Guidelines

- Use the manual upgrade approach with diff analysis (not `react-native upgrade` CLI)
- Upgrade incrementally (one major version at a time) when jumping multiple versions
- Enable New Architecture in current version before upgrading if it's required in target
- Clear all caches after upgrade (Metro, Gradle, Pods, Derived Data)
- Test thoroughly on both iOS and Android before considering upgrade complete

## Resources

- Upgrade Helper: https://react-native-community.github.io/upgrade-helper/
- RN Diff Purge: https://github.com/react-native-community/rn-diff-purge
- React Native Docs: https://reactnative.dev/docs/upgrading
- React Native Releases: https://github.com/facebook/react-native/releases

---

Start by determining the current and target versions, then proceed with research and planning before making any changes.
