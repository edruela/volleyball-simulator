# Season Management API

## Overview

The Season Management API allows you to create new seasons with dynamically configurable duration and participating countries. When a season is created, all competitions (domestic leagues, cups, and continental tournaments) are automatically scheduled for the participating countries.

## API Endpoint

### Start Season

**Endpoint:** `POST /start_season`

**Description:** Creates a new season and schedules all competitions for the specified countries and duration.

**Request Body:**
```json
{
  "seasonName": "Season 2025",
  "durationMinutes": 1440,
  "participatingCountries": ["volcania", "coastalia", "forestland"]
}
```

**Parameters:**
- `seasonName` (string, required): Name of the season
- `durationMinutes` (integer, required): Duration of the season in minutes
  - For testing: 1440 minutes (24 hours)
  - For production: 43200 minutes (30 days)
- `participatingCountries` (array, optional): List of country IDs to include in the season
  - If not provided, all 12 countries will participate
  - Valid country IDs: `volcania`, `coastalia`, `forestland`, `desertia`, `northlands`, `islandia`, `plainscountry`, `stonehills`, `riverside`, `windlands`, `sunlands`, `mistcountry`

**Response (Success):**
```json
{
  "seasonId": "uuid-string",
  "message": "Season 'Season 2025' created successfully with 156 competitions",
  "competitionsCreated": 156,
  "participatingCountries": ["volcania", "coastalia", "forestland"],
  "durationMinutes": 1440
}
```

**Response (Error):**
```json
{
  "error": "Error message describing what went wrong"
}
```

## Competition Structure

When a season is created, the following competitions are automatically scheduled:

### Domestic Competitions (Per Country)
- **Domestic Leagues**: One league for each of the 19 division tiers (16 clubs per division)
- **National Cup**: Knockout tournament including all clubs from all divisions

### Continental Competitions
- **Continental Champions League**: Elite League clubs (tier 1) from all participating countries
- **Continental Professional Cup**: Professional Division 1 clubs (tier 2) from all participating countries  
- **Continental Amateur Championship**: Semi-Pro Division 1 champions (tier 10) from all participating countries

## Countries and Modifiers

The system supports 12 fictional countries, each with unique player attribute modifiers:

1. **Volcania**: Mountainous, +15 Block Timing, +10 Strength, -5 Agility
2. **Coastalia**: Coastal, +10 Agility, +10 Serve Accuracy, -5 Strength
3. **Forestland**: Temperate, Balanced (+5 all technical skills)
4. **Desertia**: Hot climate, +15 Stamina, +5 Mental Toughness, -10 Speed
5. **Northlands**: Cold climate, +15 Spike Power, +10 Strength, -10 Agility
6. **Islandia**: Tropical, +15 Speed, +10 Court Vision, -5 Strength
7. **Plainscountry**: Agricultural, +10 Passing Accuracy, +5 Decision Making
8. **Stonehills**: Rocky terrain, +10 Injury Resistance, +10 Mental Toughness
9. **Riverside**: River valleys, +10 Adaptability, +5 all physical attributes
10. **Windlands**: Windy, +15 Ball Control, +10 Serve Accuracy
11. **Sunlands**: Sunny, +10 Stamina, +10 Jump Height, -5 night performance
12. **Mistcountry**: Foggy, +15 Court Vision, +10 Communication, -5 reaction time

## Example Usage

### Create a 24-hour test season with all countries:
```bash
curl -X POST https://your-cloud-run-url/start_season \
  -H "Content-Type: application/json" \
  -d '{
    "seasonName": "Test Season Alpha",
    "durationMinutes": 1440
  }'
```

### Create a 30-day season with specific countries:
```bash
curl -X POST https://your-cloud-run-url/start_season \
  -H "Content-Type: application/json" \
  -d '{
    "seasonName": "Championship Season 2025",
    "durationMinutes": 43200,
    "participatingCountries": ["volcania", "coastalia", "forestland", "desertia"]
  }'
```

## Data Structure

The system creates the following data structures in Firestore:

- **seasons** collection: Season metadata and configuration
- **competitions** collection: Individual competition details and participants
- **clubs** collection: Club information organized by country and division tier
- **countries** collection: Country data with player modifiers

Each season generates approximately 13 competitions per participating country plus 3 continental competitions, resulting in 159 total competitions for all 12 countries.
