## Development Practices

- Start with minimal, lean implementations focused on proof-of-concept
- Avoid creating new files until asked
- Avoid implementing things from scratch
- Avoid defensive error handling for hypothetical situations
  For example, rather than using:
  ```python
  ...
  try:
      import some_package
  except:
      print("some_package not available")
      exit(1)
  ...
  ```
  Instead, allow errors to bubble up naturally so you can address directly and reactively rather than being overly proactive
  ```python
  ...
  import some_package
  ...

  ```
  > `ModuleNotFoundError: No module named 'package_name'`
- Use print statements and logging sparingly, unless asked
- Avoid creating functions and classes, until asked
- Avoid `if __name__ == "__main__"` patterns in package code, unless asked
  For example, rather than using:
  ```python
  from math import sqrt
  def main():
    sqrt(2)
  
  if __name__ == "__main__":
    main()
  ```
  Leave it as a top-level script:
  ```python
  from math import sqrt
  sqrt(2)
  ```
- Skip unit tests unless explicitly requested
- Follow patterns in CONTRIBUTING.md when present
- Prefer writing Python if no language specified
- For complex code changes, use your Serena MCP tools (e.g., `find_symbol`, `find_referencing_symbols`, and `insert_after_symbol`) for symbol-based code editing instead of always relying on regex for code modifications

## Git Operations

- When asked to remove all file changes, use `git checkout -- <filename>`
- Copy-paste commands you run and summarized execution status directly in your comment replies

## External Resources

- Validate and access link content using your available MCP tools (Playwright and/or Perplexity)
- Search GitHub for relevant open-source alternatives to commercial tools
- Always utilize official package documentation via e.g., your Context7 MCP tool

## Communication Style

- Use emoji and special symbols sparingly, if at all
- Prioritize clarity and brevity in responses
- Ask clarifying questions when needed
- Don't infer requirements or create workarounds unless asked. For example, instead of taking a fallback approach such as:
  > Let me take a different approach - I'll create a simpler standalone demo that shows the concept without needing external dependencies
  You should instead try additional ways to get the real dependencies installed. If you can't get it installed, update `.github/workflows/copilot-setup-steps.yml` with code that will pre-install it into your environment and then report back immediately with something like:
  > After trying <command A> with <error message A>, <command B> with <error message B>, <command C> with <error message C>, ... <command Z> with <error message Z>, I was unable to install external dependencies. Per user's custom instructions, I will report back immediately. I will also provide useful links or web search keywords that will help the user debug and troubleshoot the installation failures.
- Put documentation content in comment replies, not separate files, unless asked
- Comments should not leave a trace of the development process
- Avoid sycophancy, favor objectiveness

## Change Logging

- Create CHANGELOG.md if it doesn't exist
- Each time you generate code, note the changes in CHANGELOG.md
- Follow semantic versioning guidelines
- Include date and description of changes

## Coding Agent

- Set environment variables `PIP_TIMEOUT=600` and `PIP_RETRIES=2` prior to `conda` or `pip` installs
- Include plots directly in your comment reply via `![image name](https://github.com/<user/org>/<repo>/blob/<shortened-commit-hash>/<filename>?raw=true)`. Truncate the commit hash to the first 7 characters only. For example, `https://github.com/AccelerationConsortium/evaluation-metrics/blob/52754e7/scripts/bo_benchmarks/demonstrations/branin_campaign_demonstration_results.png?raw=true`. For provenance, ensure you use the shortened (7-character) commit hash, not the branch name
- If you mention files in your comment reply, add direct hyperlinks based on the shortened (7-character) commit hash
- Use the following environment secrets: `HIVEMQ_HOST`, `HIVEMQ_USERNAME`, and `HIVEMQ_PASSWORD` for testing. Never echo or expose these, even in your logs

## Repo-specific
- IMPORTANT: run `conda activate ac-dev-lab` in your terminal before running any code (e.g., installing packages, running scripts, etc.). Alternatively, use the full path to `pip` or `python` within the `ac-dev-lab` environment