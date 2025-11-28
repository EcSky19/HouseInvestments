# HouseInvestments

A real estate investment analysis tool that scores properties based on fundamental investment metrics using the RentCast API.

## Features

- **Property Scoring Model**: Evaluates residential properties on a 0–100 scale across 5 key factors:
  - **Cap Rate** (40%) – Annual return on investment
  - **Price per Sqft** (25%) – Affordability
  - **Unit Density** (20%) – Rental income potential
  - **Property Size** (10%) – Income scale
  - **Property Type** (5%) – Rental suitability

- **Flexible Scoring**: Customize weights and thresholds for different investor profiles
- **Rent Estimates**: Fetch actual estimated rents from RentCast API for accurate cap rate calculations
- **Rich Property Data**: Integrates with RentCast public records including sale prices, tax assessments, and sale history

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from backend import score_properties_in_zipcode

# Score properties in a zip code
scores = score_properties_in_zipcode('10001', limit=20)

# Access top result
top = scores[0]
print(f"Score: {top.overall_score}/100")
print(f"Factors: {top.factors}")
print(top.explanation)
```

### With Rent Estimates (More Accurate)

```python
# Enable rent estimate fetching for real cap rate calculations
scores = score_properties_in_zipcode('10001', limit=20, include_rent_estimates=True)
```

### Custom Scoring

```python
from backend import InvestmentScorer

# Create a custom scorer for conservative investors
scorer = InvestmentScorer(
    cap_rate_weight=0.60,      # Prioritize returns
    price_per_sqft_weight=0.20,
    target_cap_rate=0.10,      # Target 10% return
    target_price_per_sqft=150  # Target $150/sqft
)

# Score a property
score = scorer.score(property_object)
```

## Configuration

Set your RentCast API key in `.env`:

```env
API_KEY=your_rentcast_api_key_here
```

## Documentation

- **[SCORING_MODEL.md](./SCORING_MODEL.md)** – Detailed explanation of scoring methodology, factors, and limitations
- **[examples.py](./examples.py)** – Code examples for common use cases

## API Integration

Uses the RentCast API to fetch:
- **Property Records**: Address, bedrooms, bathrooms, square footage, property type
- **Sale History**: Last sale price, date, and historical sales
- **Tax Data**: Tax assessments and history
- **Rent Estimates**: Market-based estimated rental income

## Score Interpretation

- **85–100**: ⭐⭐⭐⭐⭐ Excellent Investment
- **70–84**: ⭐⭐⭐⭐ Very Good Investment
- **50–69**: ⭐⭐⭐ Good Investment
- **30–49**: ⭐⭐ Fair Investment
- **0–29**: ⭐ Poor Investment

## Limitations

- **No Expense Deductions**: Cap rate calculated on gross rent (doesn't account for taxes, insurance, maintenance)
- **No Financing**: Assumes cash purchases (doesn't factor in mortgage leverage)
- **Market Assumptions**: Uses $800/bed/month as default rent estimate if RentCast estimate unavailable
- **Missing Data**: If sale price unavailable, cap rate score defaults to neutral (50)

## Future Roadmap

- Property appreciation analysis from sale history
- Neighborhood and school district integration
- Expense estimation (property taxes, insurance, maintenance)
- Multi-family property portfolio optimization
- Machine learning rent predictions
- Risk scoring based on market vacancy rates
