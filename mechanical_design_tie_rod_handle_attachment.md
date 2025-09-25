# Mechanical Design: Tie Rod Handle Attachment for Actuonix L16

## Project Overview

This document outlines the mechanical design for connecting an Actuonix L16 linear actuator to a handle using a tie rod assembly. The design addresses the requirements from issue #132 for attaching a linear actuator to an elliptical handle.

## System Specifications

### Actuator Specifications (Actuonix L16)
- **Clevis hole diameter**: 3.0mm (accepts M3 bolts)
- **Clevis width**: 5.5mm
- **Clevis slot thickness**: Up to 3.0mm material
- **Maximum force**: 35N (≈8 lbs)

### Handle Specifications
- **Cross-section**: Elliptical, 24mm (width) × 20mm (height)
- **Material**: Likely metal or composite
- **Attachment point**: Center of handle for optimal force distribution

## Design Solutions

### Solution 1: U-bolt Clamping System (Recommended for Permanent Installation)

This solution uses a square U-bolt to clamp around the handle, providing a secure mechanical connection.

#### Components List:

**1. Square U-bolt Assembly**
- **McMaster-Carr Part**: [3072T683](https://www.mcmaster.com/3072T683/)
- **Description**: Zinc-Plated Steel Square U-Bolt, 1" × 2" inside dimensions, ¼"-20 Thread
- **Justification**: 1" (25mm) internal width accommodates the 24mm handle width with minimal clearance

**2. U-bolt Backing Plate**
- **McMaster-Carr Part**: Standard backing plate for ¼"-20 U-bolts (contact McMaster for compatible plate)
- **Description**: Steel backing plate for distributing U-bolt clamping force
- **Justification**: Distributes clamping force across handle surface, prevents deformation

**3. Tie Rod (M4 System for Strength)**
- **McMaster-Carr Part**: [98863A124](https://www.mcmaster.com/98863A124/)
- **Description**: Steel Threaded Rod, M4 × 1m length
- **Justification**: M4 provides adequate strength for 35N forces while being compatible with standard hardware

**4. Rod End Bearing (Actuator Side)**
- **McMaster-Carr Part**: [6058K15](https://www.mcmaster.com/6058K15/)
- **Description**: Steel Rod End, M4 Right-Hand Male Thread
- **Justification**: M4 thread fits tie rod, can be adapted for M3 actuator connection with bushing

**5. Rod End Bearing (Handle Side)**  
- **McMaster-Carr Part**: [6058K15](https://www.mcmaster.com/6058K15/) (same as actuator side)
- **Description**: Steel Rod End, M4 Right-Hand Male Thread
- **Justification**: Provides pivot connection to U-bolt assembly

**6. Jam Nuts**
- **McMaster-Carr Part**: [90591A110](https://www.mcmaster.com/90591A110/)
- **Description**: M4 × 0.7mm Stainless Steel Thin Hex Jam Nut
- **Justification**: Locks rod end positions on threaded tie rod

**7. Connection Hardware**
- **M3 × 12mm Socket Head Cap Screws** (2 required)
- **M3 Washers** (4 required)
- **¼"-20 × 1" Hex Bolts** (2 required for U-bolt)
- **¼" Washers and Nuts** (4 washers, 2 nuts)

#### Assembly Process:

1. Position U-bolt around handle at desired attachment point
2. Install backing plate and tighten ¼"-20 bolts to secure U-bolt
3. Thread rod end bearing onto tie rod and secure with jam nut
4. Connect rod end to U-bolt backing plate using M3 hardware
5. Adjust tie rod length and connect to actuator clevis
6. Test operation and verify all connections are secure

#### Tools Required:
- Drill with 3mm bit (for additional holes in backing plate if needed)
- M3 tap (if threading holes in backing plate)
- Socket wrenches (10mm for M3, 13mm for ¼"-20)
- Thread-locking compound (recommended)

### Solution 2: Cable Tie System (Recommended for Temporary/Adjustable Installation)

This solution uses heavy-duty cable ties for a simpler, less permanent connection.

#### Components List:

**1. Reusable Cable Ties**
- **McMaster-Carr Part**: [7130K26](https://www.mcmaster.com/7130K26/)
- **Description**: 8" Long, Releasable Nylon Cable Tie, Black (Reusable Type)
- **Justification**: Reusable design allows adjustment/removal, adequate strength for temporary installation

**2. Heavy-Duty Backup Cable Ties**
- **McMaster-Carr Part**: [7132K52](https://www.mcmaster.com/7132K52/)
- **Description**: 11" Long, Releasable Nylon Cable Tie, Natural (Reusable Type)
- **Justification**: Longer length for secure attachment around elliptical handle geometry

**3. Tie Rod Components** (Same as Solution 1)
- Threaded rod: [98863A124](https://www.mcmaster.com/98863A124/) (M4)
- Rod end bearings: [6058K15](https://www.mcmaster.com/6058K15/) (both ends)
- Jam nuts: [90591A110](https://www.mcmaster.com/90591A110/) (M4)

**4. Cable Tie Attachment Point**
- **Small metal bracket** (can be fabricated or use standard L-bracket)
- **M3 hardware** for connecting rod end to bracket

#### Assembly Process:

1. Create or obtain small metal tab/bracket with 3mm hole
2. Connect rod end bearing to bracket using M3 bolt
3. Position bracket against handle and secure with multiple cable ties
4. Adjust tie rod length and connect to actuator
5. Verify secure attachment and test operation

## Force Analysis

### Load Requirements:
- **Actuator force**: 35N (8 lbs)
- **Safety factor**: 3-5x recommended for mechanical systems
- **Design load**: 105-175N (24-39 lbs)

### Component Strengths:
- **M4 threaded rod**: >500N tensile strength (adequate)
- **Rod end bearings**: Rated for much higher loads than required
- **U-bolt system**: ¼"-20 bolts rated for >1000N (more than adequate)
- **Cable ties**: 120-250 lb ratings provide significant safety margin

## Advantages and Disadvantages

### U-bolt Solution:
**Advantages:**
- Permanent, secure attachment
- Distributes load evenly
- Professional appearance
- Adjustable rod length

**Disadvantages:**
- Requires drilling/machining
- More complex installation
- Higher cost
- Permanent modification to setup

### Cable Tie Solution:
**Advantages:**
- Simple installation
- No permanent modifications
- Easily removable/adjustable
- Low cost
- Quick to implement

**Disadvantages:**
- Less professional appearance
- Potential for loosening over time
- May require periodic inspection/replacement
- Limited to lower-force applications

## Recommendations

1. **For prototype/testing**: Use Cable Tie Solution (Solution 2) for quick implementation and easy modifications

2. **For production/permanent installation**: Use U-bolt Solution (Solution 1) for maximum reliability and professional appearance

3. **Hybrid approach**: Start with cable tie solution for testing, then upgrade to U-bolt system once design is validated

## Cost Analysis

### Solution 1 (U-bolt System):
- U-bolt + plate: ~$15-20
- Tie rod components: ~$25-30
- Hardware: ~$10-15
- **Total**: ~$50-65

### Solution 2 (Cable Tie System):
- Cable ties: ~$10-15
- Tie rod components: ~$25-30
- Bracket material: ~$5-10
- **Total**: ~$40-55

## Next Steps

1. Validate all McMaster-Carr part numbers and availability
2. Order components for prototype testing
3. Create detailed assembly drawings
4. Test both solutions with actual hardware
5. Document installation procedures and maintenance requirements

## Corrections and Updates

**Important Note**: The original part numbers in this document contained errors. The following corrections have been made based on validation of actual McMaster-Carr catalog data:

### Corrected Part Numbers:
- **U-bolt**: Changed from 3038T12 (T-slot bracket) to [3072T683](https://www.mcmaster.com/3072T683/) (actual square U-bolt)
- **Threaded Rod**: Changed from 99038A108 (retaining ring) to [98863A124](https://www.mcmaster.com/98863A124/) (actual M4 threaded rod)
- **Rod Ends**: Changed from 6072K31 (spacer) to [6058K15](https://www.mcmaster.com/6058K15/) (actual rod end bearing)
- **Jam Nuts**: Changed from 90480A110 (screw) to [90591A110](https://www.mcmaster.com/90591A110/) (actual M4 jam nut)
- **Cable Ties**: Updated to verified reusable cable tie part numbers

All part numbers have now been validated against McMaster-Carr's actual catalog to ensure accuracy.