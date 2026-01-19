# PRD: Architectural Refactoring - Argelia Scraper v3.0

**Product Requirements Document - Production Level**  
**Date:** 2026-01-19  
**Author:** Neo (Senior Architect)  
**Status:** Draft for Review  
**Priority:** P0 (Blocking for Scalability)

---

## 📋 INDEX

1. [Executive Summary](#executive-summary)
2. [Context and Justification](#context-and-justification)
3. [Technical Objectives](#technical-objectives)
4. [Proposed Architecture](#proposed-architecture)
5. [Implementation Plan](#implementation-plan)
6. [Testing and QA](#testing-and-qa)
7. [Success Metrics](#success-metrics)
8. [Risks and Mitigation](#risks-and-mitigation)
9. [Timeline and Resources](#timeline-and-resources)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Current Problem

The current scraper (v2.2) works but presents **critical technical debt** that prevents:
- Scalability beyond 10 concurrent workers.
- Maintenance by distributed teams.
- Automated testing.
- Flexible configuration between environments.

### 1.2 Proposed Solution

Complete refactoring towards a **modular architecture** following SOLID principles, featuring:
- Persistent configuration system (XDG-compliant).
- Connection pooling for SQLite.
- Separation of concerns into independent modules.
- Professional logging with rotation.
- Unit and integration test suite.

### 1.3 Expected Impact

| Metric | Before | After | Improvement |
|---------|-------|---------|--------|
| Stable concurrent workers | 5 | 20 | +300% |
| Onboarding time (new dev) | 4 hours | 30 min | -87% |
| Test coverage | 0% | 85% | ∞ |
| Cross-environment config | Manual | Automatic | N/A |

---

## 2. CONTEXT AND JUSTIFICATION

### 2.1 Current Code State

**Monolithic File:** 850 lines in a single file.  
**Coupling:** High (all classes depend on each other).  
**Configuration:** Hardcoded in global constants.  
**Persistence:** SQLite connections without pooling.  
**Logging:** JSONL without rotation (risk of disk saturation).

### 2.2 Identified Pain Points

#### 🔴 Critical
1. **Hardcoded PATH without alternatives** → Users cannot choose destination.
2. **Site-specific DNS override** → Fails silently on other domains.
3. **SQLite connection leaks** → Race conditions with >10 workers.
4. **Unlimited logging** → 8GB+ files observed in production.

#### 🟡 High
5. **Mixed responsibilities** → Engine class does 7 different things.
6. **No tests** → Impossible to refactor with confidence.
7. **Non-persistent configuration** → Each execution asks for the same info.

---

## 3. TECHNICAL OBJECTIVES

### 3.1 Primary Objectives (MUST HAVE)

#### OBJ-1: Professional Configuration System
**Description:** Implement config management following XDG Base Directory Spec.  
**Success Criteria:**
- [ ] Config loadable from YAML file.
- [ ] Environment variables have priority over file.
- [ ] Interactive wizard on first run.
- [ ] Validation with Pydantic.
- [ ] Expandable paths (`~`, env vars).

**File:** `argelia_scraper/config.py`

#### OBJ-2: Connection Pool for SQLite
**Description:** Avoid race conditions and improve DB throughput.  
**Success Criteria:**
- [ ] Reusable pool of N connections (default: 5).
- [ ] Async context manager for acquire/release.
- [ ] WAL + NORMAL synchronous configuration.
- [ ] Configurable timeout per connection.
- [ ] Automatic cleanup on exit.

**File:** `argelia_scraper/db_pool.py`

#### OBJ-3: Separation of Concerns (Modular Architecture)
**Description:** Split the monolith into specialized modules.  
**Success Criteria:**
- [ ] Each module has a single responsibility.
- [ ] Testable in isolation.
- [ ] Clear interfaces between modules.
- [ ] No circular dependencies.

---

## 4. PROPOSED ARCHITECTURE

### 4.1 Component Diagram

```text
┌─────────────────────────────────────────────────┐
│                   CLI Layer                     │
│  (cli.py - Arguments + Wizard + Output)        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              Configuration Layer                │
│  (config.py - ScraperConfig + Validation)       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│               Orchestration Layer               │
│  (engine.py - ArgeliaMigrationEngine)           │
│   - Queue management                            │
│   - Worker coordination                         │
│   - Progress tracking                           │
└─────┬───────────────────────────────────┬───────┘
      │                                   │
      ▼                                   ▼
┌──────────────────┐           ┌──────────────────┐
│ Extraction Layer │           │ Persistence Layer│
│  (extractors/*)  │           │  (db_manager.py) │
│ - Text           │           │  - StateManager  │
│ - Metadata       │◄──────────┤  - SQLitePool    │
│ - Assets         │           │  - Transactions  │
└──────────────────┘           └──────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────┐
│                 Utilities Layer                 │
│  (utils/* - URL, HTML, Text processing)         │
└─────────────────────────────────────────────────┘
```

---

## 6. TESTING AND QA

### 6.1 Testing Strategy

#### Unit Tests (Target: 85% coverage)
**Tools:** pytest, pytest-asyncio, pytest-cov

**Critical Modules:**
- [ ] `config.py`: 100% (load, validation, save).
- [ ] `db_pool.py`: 95% (acquire, release, cleanup).
- [ ] `utils/url_utils.py`: 100% (URL edge cases).
- [ ] `utils/html_cleaner.py`: 90% (different types of noise).
- [ ] `extractors/text_extractor.py`: 85% (varied formats).
