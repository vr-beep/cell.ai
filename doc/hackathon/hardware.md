# Available Hardware at Monomer HQ

**Source:** Hackathon Format PDF + user confirmation

## Robotic Workcell

| Equipment | Description |
|---|---|
| **Opentrons Flex** | Liquid handler — mixes media, performs media exchanges |
| **Liconic LPX-220 Carousel** | Plate storage carousel |
| **Liconic STX-110** | 4C Incubator (cold storage) |
| **Liconic STX-220** | 37C Incubator (growth incubation) |
| **Tecan Infinite** | Plate reader — OD600 absorbance readout |
| **KX-2 Robotic Arm** | Moves plates between instruments |

## MCP Actions Available

All robotic actions are accessed via Monomer's MCP (Model Context Protocol):

| Action | Description |
|---|---|
| **Create media mixture** | Robot mixes specified composition using Opentrons Flex |
| **Media exchange** | Robot applies new media to wells |
| **Incubate** | Robot moves plate to STX-220 for specified time. Temperature controllable via MCP (default 37C for V. natriegens). |
| **Plate read** | Robot reads OD600 via Tecan Infinite plate reader |

## Notes

- No microscope available — OD600 (absorbance) is the primary readout
- Fluorescence may also be available via Tecan Infinite (confirm day-of)
- V. natriegens grows at 37C, so STX-220 is the relevant incubator
- STX-110 (4C) useful for storing prepared plates/reagents
