"""
Example usage of the investment scoring model.

Run this file to see the scorer in action:
  python3 examples.py
"""

from backend import (
    score_properties_in_zipcode,
    InvestmentScorer,
    fetch_properties,
    fetch_rent_estimate
)


def example_1_basic_scoring():
    """Example 1: Score properties in a zip code."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Score Properties in a Zip Code")
    print("=" * 70)
    
    zip_code = '10001'  # New York
    scores = score_properties_in_zipcode(zip_code, limit=5)
    
    print(f"\nTop 3 investments in {zip_code}:\n")
    for i, score in enumerate(scores[:3], 1):
        print(f"{i}. Score: {score.overall_score}/100")
        print(f"   Property ID: {score.property_id}\n")


def example_2_custom_weights():
    """Example 2: Use a custom-weighted scorer."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Custom Scoring Weights")
    print("=" * 70)
    
    # Create a scorer that heavily weights cap rate (conservative investor)
    conservative_scorer = InvestmentScorer(
        cap_rate_weight=0.60,
        price_per_sqft_weight=0.20,
        unit_density_weight=0.10,
        size_weight=0.05,
        property_type_weight=0.05,
        target_cap_rate=0.10  # Require 10% return
    )
    
    # Create a scorer for growth investors (property appreciation focus)
    growth_scorer = InvestmentScorer(
        cap_rate_weight=0.20,
        price_per_sqft_weight=0.30,
        unit_density_weight=0.20,
        size_weight=0.20,
        property_type_weight=0.10
    )
    
    # Fetch a property
    props = fetch_properties('78244', limit=1)
    if props:
        prop = props[0]
        
        conservative = conservative_scorer.score(prop)
        growth = growth_scorer.score(prop)
        
        print(f"\nSame property, different investor profiles:\n")
        print(f"Conservative Investor Score: {conservative.overall_score}/100")
        print(f"Growth Investor Score: {growth.overall_score}/100")
        print(f"\nProperty: {prop.address}")
        print(f"  {prop.bedrooms}bd/{prop.bathrooms}ba | {prop.square_footage} sqft")


def example_3_rent_estimate():
    """Example 3: Fetch actual rent estimates for cap rate."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Rent Estimate-Based Scoring")
    print("=" * 70)
    
    zip_code = '78244'
    props = fetch_properties(zip_code, limit=2)
    scorer = InvestmentScorer()
    
    print(f"\nScoring {len(props)} properties with rent estimates:\n")
    
    for prop in props:
        # Try to fetch actual rent estimate
        rent_est = fetch_rent_estimate(
            prop.address.split(',')[0],
            prop.city,
            prop.state
        )
        
        if rent_est:
            score = scorer.score(prop, estimated_monthly_rent=rent_est)
            print(f"Property: {prop.address}")
            print(f"  Estimated Monthly Rent: ${rent_est:,.0f}")
            print(f"  Investment Score: {score.overall_score}/100\n")
        else:
            score = scorer.score(prop)
            print(f"Property: {prop.address}")
            print(f"  Rent estimate unavailable (using default)")
            print(f"  Investment Score: {score.overall_score}/100\n")


def example_4_filtering():
    """Example 4: Filter by score range."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Filter Properties by Score Range")
    print("=" * 70)
    
    scores = score_properties_in_zipcode('78244', limit=10)
    
    excellent = [s for s in scores if s.overall_score >= 85]
    good = [s for s in scores if 50 <= s.overall_score < 70]
    poor = [s for s in scores if s.overall_score < 30]
    
    print(f"\nOut of {len(scores)} properties:")
    print(f"  Excellent (85+): {len(excellent)}")
    print(f"  Good (50-70): {len(good)}")
    print(f"  Poor (<30): {len(poor)}")


if __name__ == '__main__':
    print("\n🏠 Investment Scoring Model Examples")
    
    # Uncomment to run individual examples:
    example_1_basic_scoring()
    # example_2_custom_weights()
    # example_3_rent_estimate()
    # example_4_filtering()
    
    print("\n✓ Done!")
