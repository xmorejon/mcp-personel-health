# MCP Personal Health Agent — Project Context

## Project

- Name: mcp-personel-health
- GCP Project ID: mcp-personel-health
- Stack: Google ADK + Firestore Remote MCP + Cloud Run + Google Actions

## Firestore Database Schema

> Source of truth — do NOT suggest creating or modifying collections.
> This database already exists and has real data.

# Firestore Schema Summary

- **Collection:** `health_metrics`
  - **Fields:**
    - `date` (string): _e.g., 2026-05-20_
    - `averageHeartRate` (number): _e.g., 72_
    - `steps` (number): _e.g., 3969_
    - `lastUpdated` (timestamp): _e.g., {"\_seconds":1779399009,"\_nanoseconds":850000000}_
    - `weight` (number): _e.g., 86.2_
    - `activities` (array): _e.g., [{"activeTimeSecs":903,"distanceKm":1.1935201,"..._

## Rules for this project

- Always use read-only Firestore MCP tools: get_document, list_documents, list_collections
- All agent responses must be voice-friendly (no markdown, no bullet points)
- Never expose raw Firestore field names in spoken responses
- Authentication uses ADC (Application Default Credentials)
