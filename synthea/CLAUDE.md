# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synthea is a Synthetic Patient Population Simulator that generates realistic (but not real) patient data and health records in multiple formats (FHIR R4/STU3/DSTU2, C-CDA, CSV, CPCDS). It simulates the lifecycle of patients from birth to death, including encounters, conditions, medications, procedures, and more.

## Build System

Synthea uses Gradle as its build tool. The project requires Java JDK 11 or newer (LTS versions 11 or 17 recommended).

### Common Commands

Build and test:
```bash
./gradlew build check test
```

Build only (no tests):
```bash
./gradlew assemble
```

Run all tests:
```bash
./gradlew test
```

Run a single test class:
```bash
./gradlew test --tests "org.mitre.synthea.engine.GeneratorTest"
```

Run a single test method:
```bash
./gradlew test --tests "org.mitre.synthea.engine.GeneratorTest.testGeneratePerson"
```

Clean build artifacts:
```bash
./gradlew clean
```

Code quality checks (includes checkstyle and jacoco):
```bash
./gradlew check
```

### Running Synthea

Generate synthetic patients:
```bash
./run_synthea
```

Generate patients with options:
```bash
./run_synthea -p 100 Massachusetts
./run_synthea -s 12345 -p 10 --exporter.csv.export=true
```

Run via Gradle:
```bash
./gradlew run
./gradlew run -Params="['-p', '100', 'Massachusetts']"
```

### Specialized Tasks

Generate graphical visualizations of modules:
```bash
./gradlew graphviz
```

List all simulated concepts:
```bash
./gradlew concepts
```

List patient attributes:
```bash
./gradlew attributes
```

Test physiology simulation:
```bash
./gradlew physiology
```

Apply FHIR transformations (Flexporter):
```bash
./gradlew flexporter -Params="['arg1', 'arg2']"
```

## Architecture

### Core Packages

- **org.mitre.synthea.engine**: Core simulation engine
  - `Generator`: Main entry point for population generation. Manages timesteps and coordinates Person lifecycle
  - `Module`: Generic module framework for disease/condition modeling. Modules are state machines defined in JSON
  - `State`: Individual states within modules (conditions, procedures, transitions, etc.)
  - `Logic`: Evaluation engine for conditional logic in modules
  - `PhysiologySimulator`: SBML-based physiological modeling system

- **org.mitre.synthea.world.agents**: Agent-based modeling
  - `Person`: Core patient entity with attributes, health record, demographics, and module history
  - `Provider`: Healthcare providers and facilities
  - `Payer`: Insurance payers and coverage plans
  - `PayerManager`: Global payer registry and management

- **org.mitre.synthea.world.concepts**: Domain concepts
  - `HealthRecord`: Patient medical record with encounters, conditions, medications, procedures, observations, etc.
  - `VitalSign`: Enumeration of vital signs (height, weight, BMI, BP, etc.)
  - `Costs`: Cost calculations for procedures and medications
  - `BirthStatistics`: Demographics and birth-related statistics

- **org.mitre.synthea.world.geography**: Geographic and demographic data
  - `Demographics`: Population demographics by location
  - `Location`: Geographic location modeling

- **org.mitre.synthea.modules**: Java-based modules (complement JSON modules)
  - `LifecycleModule`: Birth, aging, and death
  - `EncounterModule`: Encounter scheduling and types
  - `HealthInsuranceModule`: Insurance enrollment and coverage
  - `DeathModule`: Death processing and causes

- **org.mitre.synthea.export**: Export to various formats
  - `Exporter`: Main export coordinator
  - `FhirR4`, `FhirStu3`, `FhirDstu2`: FHIR exporters for different versions
  - `CCDAExporter`: C-CDA export
  - `CSVExporter`: CSV export
  - `CPCDSExporter`: CPCDS format export
  - `flexporter/`: Flexible FHIR mapping and transformation framework

- **org.mitre.synthea.helpers**: Utilities and helpers
  - `Config`: Configuration management (loads from synthea.properties)
  - `RandomNumberGenerator`: Seeded random generation for reproducibility
  - `Utilities`: Common utility functions
  - `Concepts`: Concept extraction and analysis

- **org.mitre.synthea.identity**: Identity and entity management
  - `Entity`: Identity records with variants over time
  - `EntityManager`: Manages patient identities

### Generic Module Framework

The heart of Synthea is the Generic Module Framework - disease and condition models defined as JSON state machines:
- Located in `src/main/resources/modules/`
- Each module is a directed graph of states with transitions
- State types include: Initial, Terminal, Delay, Guard, CallSubmodule, Encounter, ConditionOnset, ConditionEnd, MedicationOrder, Procedure, Observation, etc.
- Transitions can be conditional (based on age, gender, attributes, logic expressions)
- Modules can call other modules as submodules
- See [Generic Module Framework wiki](https://github.com/synthetichealth/synthea/wiki/Generic-Module-Framework) for details

### Data Flow

1. **Generator** creates a population for a location and time period
2. For each **Person**, the Generator runs simulation timesteps (default: 7 days)
3. At each timestep:
   - Java modules (Lifecycle, Encounter, etc.) run first
   - Generic JSON modules process based on current state
   - States evaluate transitions and advance
   - Health record is updated with new entries
4. After simulation completes, **Exporter** writes records in configured formats
5. Output files go to `./output/` (configurable via synthea.properties)

### Configuration

Main configuration file: `src/main/resources/synthea.properties`
- Controls which exporters are enabled
- Sets population demographics and statistics sources
- Configures output directories and file naming
- Can be overridden via command line: `--exporter.fhir.export=true`
- Can load custom config files: `-c /path/to/config.properties`

### Testing

Tests are in `src/test/java/org/mitre/synthea/`
- Uses JUnit 4 with Mockito and PowerMock
- Test coverage tracked with Jacoco
- Tests require up to 6GB heap: configured in build.gradle
- Helper classes: `TestHelper`, `PersonTester`, `FailedExportHelper`

## Important Notes

- Always compile code before marking work as complete
- Main class entry points should end with `System.exit(0)`
- Do not run Java code directly (especially in src/main/java) - it typically fails
- Random number generation is seeded for reproducibility - use Person's RNG methods, not Math.random()
- Time is represented as milliseconds since epoch
- Module state machines must have exactly one Initial state and at least one Terminal state
- FHIR resources can be validated against profiles - validation resources included for R4, STU3, DSTU2

## Key Design Patterns

- **Modular Disease Modeling**: Conditions and diseases are isolated JSON state machines that can be composed
- **Deterministic Simulation**: Given same seed, generates identical populations for reproducibility
- **Timestep-based Processing**: Discrete time simulation advances in configurable timesteps
- **Pluggable Exporters**: Multiple export formats supported through common Exporter interface
- **Attribute-based State**: Person attributes drive module logic and transitions
