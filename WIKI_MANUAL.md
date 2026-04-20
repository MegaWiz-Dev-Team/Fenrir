# Fenrir — Asgard User Manual

## System Overview
CI/CD and GitOps Executor. Scrapes and automates deployment flows inside the cluster bounds.

This repository is an integral node of the **Asgard AI Ecosystem**. It operates securely inside the native K3s cluster.

## Architecture
```mermaid
graph TD;
    API[External Request] --> Gateway[Ingress Controller];
    Gateway --> Fenrir[Fenrir Pod];
    Fenrir --> MCP[Hermodr Sidecar];
    MCP --> InternalDB[(Internal Data Source)];
```

## Setup & Deployment
To deploy Fenrir natively within the K3s environment, navigate to the Asgard root and execute:
```bash
./scripts/k3s-deploy.sh fenrir
```
*Note: In SIT/Local iterations, this service resolves internally at `fenrir.asgard.internal` via local `/etc/hosts` DNS configuration.*

## MCP Integration Strategy (Read-only Boundary)
In alignment with platform security parameters, the MCP toolsets exposed by Fenrir through the Hermodr sidecar are explicitly restricted to **GET**, **LIST**, and **CHECK** capabilities. 

All transaction-mutating tools (POST/PUT/DELETE) remain structurally disabled at the MCP edge tier to ensure agent immutability during preliminary cluster staging.

## Interface & Usage Flow
*Visual guides and interface demonstrations (where applicable) are appended beneath this line.*


