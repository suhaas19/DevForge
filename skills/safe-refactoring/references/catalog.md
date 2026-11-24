# Refactoring catalog (the ones agents need most)

Names follow Fowler's *Refactoring* (2nd ed.) so commit messages are searchable.

| Smell | Refactoring | Safe-step recipe |
|---|---|---|
| Long function | **Extract Function** | Copy the fragment into a new function, pass needed variables as parameters, return what callers use, replace the fragment with a call, run tests. |
| Unclear name | **Rename Variable/Function/Field** | Use LSP/IDE rename; for public names, add the new name, delegate the old one to it, migrate callers, remove the old one last. |
| Long parameter list | **Introduce Parameter Object** | Create the object, add it as an optional parameter, migrate callers one by one, remove old parameters. |
| Duplicated code | **Extract Function / Slide Statements** | Make the duplicates identical first (small edits, tests green), then extract once. |
| Big class / module | **Extract Class / Move Function** | Move one cohesive group at a time; leave a re-export at the old location until callers are updated. |
| Conditional on type | **Replace Conditional with Polymorphism** | Introduce the type hierarchy with the switch still in place, move one branch at a time. |
| Nested conditionals | **Replace Nested Conditional with Guard Clauses** | Invert one condition at a time, return early. |
| Global/shared state | **Encapsulate Variable** | Route all reads/writes through accessors first; then change the storage. |
| Temporary field / flag argument | **Split Function / Remove Flag Argument** | Create one function per flag value, delegate the flagged one, migrate callers. |
| Primitive obsession (money as float, IDs as str) | **Replace Primitive with Object** | Wrap at the boundary, propagate inward. |
| Inheritance misuse | **Replace Subclass with Delegate** | Add the delegate, forward calls, remove the subclass. |

## Parallel change (expand → migrate → contract)
For anything with external callers (public APIs, DB columns, event schemas, config keys):
1. **Expand:** add the new form alongside the old; both work.
2. **Migrate:** move callers/data to the new form, in as many steps as needed.
3. **Contract:** remove the old form once nothing uses it.
Each phase is separately deployable and reversible.

## Mikado method (for tangled changes)
1. Try the goal change directly (in a scratch branch, time-boxed).
2. When it breaks, note each prerequisite change that would have made it work; draw them as a graph under the goal.
3. **Revert everything.**
4. Pick a leaf prerequisite, do it on a clean tree, test, commit.
5. Repeat until the goal change is a small, safe step.

## Strangler fig (for replacing a subsystem)
Route calls through a facade; send a growing share of traffic or features to the new implementation behind the facade; delete the old one when it receives nothing.

## Branch by abstraction
Introduce an interface in front of the code being replaced, switch callers to the interface, build the new implementation behind it, flip over, remove the old one. Keeps trunk shippable throughout.
