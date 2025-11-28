# Investment Scoring Model

## Overview

The investment scoring model in `backend.py` evaluates residential real estate properties across multiple financial and structural factors to produce a 0–100 investment quality score.

**Score Interpretation:**
- **0–30**: Poor investment
- **30–50**: Fair investment  
- **50–70**: Good investment
- **70–85**: Very good investment
- **85–100**: Excellent investment

---

## Scoring Factors

### 1. **Cap Rate (40% weight)**
- **Formula**: Annual Rental Income ÷ Property Purchase Price
- **Data Source**: 
  - Sale price from RentCast property records (`lastSalePrice`)
  - Estimated monthly rent from RentCast rent API (`/v1/avm/rent`)
  - Or estimated based on bedrooms ($800/bed/month if no estimate available)
- **Scoring**: Peaks at ~8% cap rate; higher rates score higher (with diminishing returns above 8%)
- **Why it matters**: Cap rate is the most fundamental real estate investment metric. It directly measures annual cash-on-cash return.

### 2. **Price Per Square Foot (25% weight)**
- **Formula**: Last Sale Price ÷ Square Footage
- **Data Source**: `lastSalePrice` and `squareFootage` from RentCast API
- **Scoring**: Optimal at $200/sqft; lower is better (more affordable)
- **Why it matters**: Indicates overall affordability and value relative to market comps

### 3. **Unit Density (20% weight)**
- **Formula**: (Bedrooms + Bathrooms) ÷ Square Footage × 100
- **Data Source**: `bedrooms`, `bathrooms`, `squareFootage` from API
- **Scoring**: Optimal at ~0.35 units per 100 sqft; penalizes both under- and over-density
- **Why it matters**: Measures rental income potential per unit of space; very high density indicates overcrowding

### 4. **Property Size (10% weight)**
- **Data Source**: `squareFootage`
- **Scoring**: 
  - Below 800 sqft: 20/100 (too small)
  - 800–2000 sqft: Linear ramp (20→100)
  - Above 2000 sqft: 100/100 (optimal)
- **Why it matters**: Larger properties generate higher absolute rental income

### 5. **Property Type (5% weight)**
- **Data Source**: `propertyType` from API
- **Scoring by Type**:
  - Apartment / Multi-Family: **95** (best for rentals)
  - Condo: **90**
  - Townhouse: **85**
  - House: **70**
  - Mobile Home: **75**
  - Land: **40** (no rental income)
  - Commercial: **60**
- **Why it matters**: Some property types are inherently better suited for rental investment

---

## Usage

### Basic Scoring
```python
from backend import score_properties_in_zipcode

# Fetch and score properties in a zip code
scores = score_properties_in_zipcode('78244', limit=20)

# Print top result
top = scores[0]
print(top.explanation)
print(f"Overall Score: {top.overall_score}")
print(f"Factors: {top.factors}")
```

### Scoring with Rent Estimates
For more accurate cap rate calculations, enable rent estimate fetching (slower, makes additional API calls):

```python
# Fetch actual rent estimates for cap rate calculation
scores = score_properties_in_zipcode('78244', limit=20, include_rent_estimates=True)
```

### Custom Scorer Configuration
```python
from backend import InvestmentScorer, Property

scorer = InvestmentScorer(
    cap_rate_weight=0.50,           # Increase weight on cap rate
    price_per_sqft_weight=0.20,     # Decrease weight on affordability
    target_cap_rate=0.10,            # Target 10% instead of 8%
    target_price_per_sqft=150        # Target $150/sqft
)

# Score a single property
property = Property(...)
score = scorer.score(property, estimated_monthly_rent=1500)
```

---

## Data Fields Used

| Field | Source | Used For |
|-------|--------|----------|
| `lastSalePrice` | Public records | Cap rate, price/sqft |
| `lastSaleDate` | Public records | (Informational) |
| `squareFootage` | Property records | Price/sqft, unit density, size |
| `bedrooms` | Property records | Cap rate estimate, unit density, size potential |
| `bathrooms` | Property records | Unit density |
| `propertyType` | Property records | Property type score |
| `taxAssessments` | Tax records | Informational (not currently used in score) |

---

## API Endpoints Used

1. **Property Records**: `GET /v1/properties?zipCode=...`
   - Returns property details, sale price, tax assessments

2. **Rent Estimate** (optional): `GET /v1/avm/rent?address=...&city=...&state=...`
   - Returns estimated monthly rent (more accurate than bedrooms-based estimate)

---

## Limitations & Assumptions

1. **No Sale Price Available**: If `lastSalePrice` is `None`, cap rate and price/sqft scores default to 50 (neutral). This can happen for properties that haven't sold recently.

2. **Rent Estimation**: Without API rent estimates, rent is assumed at $800/month per bedroom. This is a market average; actual rents vary significantly by location.

3. **Expenses Not Included**: The cap rate calculation only considers gross rental income, not property taxes, insurance, maintenance, or vacancy rates. Real investors should deduct these.

4. **Market Trends**: The model doesn't account for appreciation potential, market momentum, or location desirability beyond property type.

5. **Financing Ignored**: The model assumes cash purchases. Leveraged investments (mortgages) could have very different returns.

---

## Future Enhancements

- Integrate property appreciation history from sale records
- Add neighborhood/school district ratings via external APIs
- Include estimated annual expenses (taxes, insurance, maintenance)
- Factor in distance to job centers or transit
- Use machine learning to predict rent rather than simple estimates
- Add risk scoring (e.g., high vacancy rates in area)
