# Command line

The `hostlens` command is installed with the Python package

```bash
hostlens --help
```

The CLI calls the same `HostLens` methods as the Python API

## Identify one address

```bash
hostlens identify 192.168.1.20
hostlens identify 192.168.1.20 --deep
```

The command prints known identity fields and the overall confidence

## Scan a network

Use the detected local subnet

```bash
hostlens scan
```

Choose a mode

```bash
hostlens scan --fast
hostlens scan --deep
```

Pass a subnet explicitly

```bash
hostlens scan 192.168.1.0/24
```

`--fast` and `--deep` cannot be used together

The scan command prints an address as soon as it is found, then prints the completed profile after enrichment

## Quick discovery

```bash
hostlens discover
hostlens discover 192.168.1.0/24
```

This uses fast mode and prints the resulting profiles

## Passive watch

```bash
hostlens watch --passive
hostlens watch 192.168.1.0/24 --passive
```

Stop the command with `Ctrl+C`

## Run without the console script

This is useful when checking which Python environment contains HostLens

```bash
python -m hostlens.cli --help
```

If `python -m hostlens.cli` works but `hostlens` does not, the virtual environment is probably inactive or its scripts directory is missing from `PATH`
