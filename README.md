# DNSCacher

**DNSCacher** is a command-line utility that helps you manage domain-to-IP
mappings efficiently. It supports caching results in a local file, updating
those results on demand, removing stale entries, and refreshing entries in
user-defined parts of the cache. Additionally, it can produce various output
formats (e.g., mappings, IP addresses, domain lists, and ipset commands) to
standard output.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Commands](#commands)
   - [GET](#get)
   - [ADD](#add)
   - [UPDATE](#update)
   - [REFRESH](#refresh)
5. [Options](#options)
6. [Output Formats](#output-formats)
7. [Logging](#logging)
8. [Error Handling](#error-handling)
9. [Examples](#examples)
10. [License](#license)

---

## Features

- **Domain-to-IP Caching**  
  Store resolved IP addresses for a list of domains, preventing repeated DNS
  lookups.

- **Incremental Updates**  
  Only resolves domains that are not yet in your cache. Removes stale domains
  that no longer appear in your source list.

- **Partial Refresh**  
  Re-resolve only a random subset (percentage) of your cached domains to keep
  them fresh without resolving everything every time.

- **Multiple Output Formats**  
  Can output mappings, IP addresses, domain lists, or an ipset command.

- **Parallelism**  
  Specify a number of parallel jobs (`--jobs`) to resolve domains concurrently.

---

## Installation

```bash
pip install dnscacher
```

or

Clone the repository and install it locally:

```bash
pip install .
```

---

If you want to develop the code, you can install the development dependencies
by running:

```bash
pip install -e ".[dev]"
```

This will install the development dependencies together with the package in
editable mode.

## Usage

Run the `dnscacher` command with one of the subcommands:

```bash
dnscacher [OPTIONS] {get|add|update|refresh} [SOURCE]
```

- The `SOURCE` is either a local file or a URL and is not needed for the `get`
  or `refresh` commands.

### Basic Workflow

1. **Add** a new source of domains or start from an existing one.
2. **Update** to handle changes in a domain list.
3. **Get** the stored cache data to your console.
4. **Refresh** in parts to re-resolve subsets of the cache if needed.

---

## Commands

Below are the primary commands. Each command also accepts common options
described in [Options](#options).

### GET

**Command:** `dnscacher get`

- **Description:**  
  Retrieves the current domain-to-IP mappings from the cache and (optionally)
  prints them to stdout in the format(s) you choose.

- **Key Points:**
  - Does **not** resolve or remove domains.
  - Use `--output` to choose what you want to see: e.g., `mappings`, `ips`,
    `domains`, or `ipset`.

### ADD

**Command:** `dnscacher add [SOURCE]`

- **Description:**  
  Resolves and **adds** any domains not already in the cache.  
  If the `--debug` flag is set, the `SOURCE` is ignored, and `debug.txt` is used.

- **Behavior:**
  - Reads from `SOURCE` (URL or file).
  - Only **new** domains (compared to the existing cache) are resolved.
  - The newly resolved IPs are appended to the cache.
  - Does **not** remove any domains already in the cache.

### UPDATE

**Command:** `dnscacher update [SOURCE]`

- **Description:**  
  Combines adding new domains and removing stale domains in one step.

- **Behavior:**
  - Reads from `SOURCE` (URL or file).
  - Resolves any **new** domains, just like in **ADD**.
  - **Removes** any domains from your cache that are no longer in `SOURCE`.
  - Maintains the rest of the domains.

### REFRESH

**Command:** `dnscacher refresh`

- **Description:**  
  Re-resolves a random set (size is given by `--part`) of **already cached**
  domains.

- **Behavior:**
  - Does **not** add or remove domains, only re-resolves ones that exist in the
    cache.
  - Useful if you want to verify that the IPs in your cache are still correct,
    without re-resolving **all** of them.

---

## Options

To get get information on the options run the `dnscacher --help` command.

#### Source Argument

- Some commands like **ADD** or **UPDATE** optionally take a `SOURCE` argument.
- This `SOURCE` can be:
  - A local file path (e.g., `/path/to/file.txt`)
  - A URL (e.g., `https://example.com/domains.txt`)
- If the `--debug` flag is set, the `SOURCE` provided is ignored, and the tool
  uses the local `debug.txt` file from the project.

---

## Output Formats

Use `-o/--output` with one or more comma-separated values:

- **`mappings`**: Prints the domain followed by all its IP addresses (e.g.,
  `example.com 93.184.216.34`).
- **`ips`**: Prints only the IP addresses in the cache, one per line.
- **`domains`**: Prints only the domains in the cache, one per line.
- **`ipset`**: Prints `add <ipsetName> <ip>` lines. Useful for piping into
  `ipset` commands.

If you provide multiple outputs, separate them with commas:

```bash
dnscacher --output mappings,ipset get
```

That will print the mappings block, then the ipset block.

---

## Examples

### 1. Add a List of Domains from a URL

```bash
dnscacher add https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn-only/hosts
```

- Resolves all new domains found in that URL and appends them to the cache.

### 2. Get the Current Mappings in `ipset` Format

```bash
dnscacher --output ipset get
```

- Prints lines of the form `add dnscacher 93.184.216.34`.

### 3. Update Cache from a Local File

```bash
dnscacher update /path/to/domains.txt
```

- Adds any new domains from `domains.txt` and removes any that no longer appear
  in it.

### 4. Refresh 50% of Cached Domains

```bash
dnscacher --part 50 refresh
```

- Randomly picks 50% of the cached domains and re-resolves them, updating the
  cache with potentially new IP addresses.
