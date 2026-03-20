# RFC 0004: Effects

## Status
Draft

## Summary

Define Astra's explicit effect model.

## Proposed rule

Every executable artifact is either:

- `pure`, or
- `effects [...]`

## Initial effect taxonomy

- db.read
- db.write
- emit
- http.call
- mail.send
- fs.read
- fs.write
- clock
- ids
- schedule
- await.signal
- ui.prompt

## Why

This enables:

- safer static analysis
- deterministic workflow validation
- emitter reasoning
- AI-guided safe modifications
