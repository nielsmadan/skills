# Framework Detection & Terminology

## Framework Detection

Check for the following config patterns to detect the project's test framework:

- `jest.config.*`, `package.json` with jest → Jest
- `vitest.config.*` → Vitest
- `pytest.ini`, `pyproject.toml` with pytest → pytest
- `*_test.go` files → Go testing
- `*_test.dart` files → Flutter test
- `.rspec`, `Gemfile` with rspec → RSpec
- `Cargo.toml` with `[dev-dependencies]` → Rust `#[test]`
- `*.test.tsx` or `*.spec.tsx` with `@testing-library/react` in package.json → React Testing Library
- `phpunit.xml` → PHPUnit

---

## Framework Terminology Mapping

When reviewing or generating tests, translate concepts to the detected framework:

| Concept | Jest/Vitest | pytest | Go testing | Flutter test |
|---------|-------------|--------|------------|--------------|
| Test suite grouping | `describe()` | class or module | `func Test...` prefix | `group()` |
| Individual test | `it()` / `test()` | `def test_...()` | `func Test...(t *testing.T)` | `test()` / `testWidgets()` |
| Setup (per-test) | `beforeEach()` | `setup_method` / fixture | `t.Cleanup()` or helper | `setUp()` |
| Setup (per-suite) | `beforeAll()` | `setUpClass` / session fixture | `TestMain()` | `setUpAll()` |
| Mocking | `jest.mock()` | `unittest.mock.patch` | interface + stub struct | `mockito` package |
| Assertion | `expect(x).toBe(y)` | `assert x == y` | `if got != want { t.Errorf() }` | `expect(x, equals(y))` |
| Async test | `async/await` | `@pytest.mark.asyncio` | `t.Run` with goroutines | `async` test + `pump()` |
| Skip test | `it.skip()` | `@pytest.mark.skip` | `t.Skip()` | `skip()` |

Use this table to adapt all examples and checklists in the skill. Code examples in the skill use JavaScript/Jest syntax as a reference; translate idioms to the detected framework.
