from dotenv import load_dotenv
import os
import httpx
from typing import Optional, Dict, List
from dataclasses import dataclass

load_dotenv()

api_key = os.getenv("API_KEY")


@dataclass
class Property:
    """Represents a property from the RentCast API."""
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str
    bedrooms: int
    bathrooms: int
    square_footage: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[str] = None
    estimated_annual_rent: Optional[float] = None
    tax_assessment_value: Optional[float] = None
    
    @classmethod
    def from_api(cls, data: dict) -> 'Property':
        """Create a Property from API response data."""
        # Get latest tax assessment if available
        tax_value = None
        if 'taxAssessments' in data and data['taxAssessments']:
            latest_year = max(data['taxAssessments'].keys())
            tax_value = data['taxAssessments'][latest_year].get('value')
        
        return cls(
            id=data.get('id'),
            address=data.get('formattedAddress'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zipCode'),
            property_type=data.get('propertyType'),
            bedrooms=data.get('bedrooms', 0),
            bathrooms=data.get('bathrooms', 0),
            square_footage=data.get('squareFootage', 0),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            last_sale_price=data.get('lastSalePrice'),
            last_sale_date=data.get('lastSaleDate'),
            estimated_annual_rent=None,  # Will be fetched separately if needed
            tax_assessment_value=tax_value
        )


@dataclass
class InvestmentScore:
    """Result of investment scoring."""
    property_id: str
    overall_score: float  # 0-100
    factors: Dict[str, float]  # individual factor scores
    explanation: str


class InvestmentScorer:
    """
    Scores properties based on real estate investment fundamentals.
    
    Scoring considers:
    - Cap rate (annual rental income / property price)
    - Price per square foot (affordability)
    - Unit density (bedrooms/bathrooms relative to size)
    - Property size (larger properties = higher income potential)
    - Property type (apartments typically better for rentals)
    """
    
    def __init__(
        self,
        cap_rate_weight: float = 0.40,
        price_per_sqft_weight: float = 0.25,
        unit_density_weight: float = 0.20,
        size_weight: float = 0.10,
        property_type_weight: float = 0.05,
        # Thresholds for scoring (adjust based on market)
        target_price_per_sqft: float = 200,  # Optimal price per sqft
        target_cap_rate: float = 0.08,  # Target 8% cap rate
        min_bedrooms: int = 2,
        min_bathrooms: int = 1,
        min_sqft: int = 800,
        ideal_sqft: int = 2000
    ):
        self.cap_rate_weight = cap_rate_weight
        self.price_per_sqft_weight = price_per_sqft_weight
        self.unit_density_weight = unit_density_weight
        self.size_weight = size_weight
        self.property_type_weight = property_type_weight
        
        self.target_price_per_sqft = target_price_per_sqft
        self.target_cap_rate = target_cap_rate
        self.min_bedrooms = min_bedrooms
        self.min_bathrooms = min_bathrooms
        self.min_sqft = min_sqft
        self.ideal_sqft = ideal_sqft
    
    def score(self, property: Property, estimated_monthly_rent: Optional[float] = None) -> InvestmentScore:
        """
        Calculate investment score for a property.
        
        Args:
            property: Property object to score
            estimated_monthly_rent: Optional monthly rent estimate (if not provided, estimated from market data)
        
        Returns a score from 0-100 where:
        - 0-30: Poor investment
        - 30-50: Fair investment
        - 50-70: Good investment
        - 70-85: Very good investment
        - 85-100: Excellent investment
        """
        factors = {}
        
        # 1. Cap Rate Score (if we have price data)
        # Cap Rate = Annual Rental Income / Property Price
        if property.last_sale_price and property.last_sale_price > 0:
            # Estimate annual rent (use provided rent or estimate based on unit density and market)
            if estimated_monthly_rent:
                annual_income = estimated_monthly_rent * 12
            else:
                # Estimate rent based on bedrooms as proxy
                # Typical: $500-1500 per bedroom per month depending on location
                annual_income = property.bedrooms * 800 * 12  # Conservative estimate
            
            cap_rate = annual_income / property.last_sale_price
            cap_rate_score = self._score_cap_rate(cap_rate)
            factors['cap_rate'] = cap_rate_score
        else:
            factors['cap_rate'] = 50  # Neutral score if no price data
        
        # 2. Price per square foot score (affordability)
        if property.last_sale_price and property.square_footage > 0:
            price_per_sqft = property.last_sale_price / property.square_footage
            price_score = self._score_price_per_sqft(price_per_sqft)
        else:
            price_score = 50  # Neutral if no data
        factors['price_per_sqft'] = price_score
        
        # 3. Unit density score (bedrooms + bathrooms relative to size)
        # More beds/baths in reasonable space = better rental income potential
        unit_density_score = self._score_unit_density(
            property.bedrooms,
            property.bathrooms,
            property.square_footage
        )
        factors['unit_density'] = unit_density_score
        
        # 4. Property size score
        # Larger properties = higher absolute rental income potential
        size_score = self._score_size(property.square_footage)
        factors['property_size'] = size_score
        
        # 5. Property type score
        # Some types are better for rental income
        property_type_score = self._score_property_type(property.property_type)
        factors['property_type'] = property_type_score
        
        # Calculate weighted overall score
        overall_score = (
            factors['cap_rate'] * self.cap_rate_weight +
            factors['price_per_sqft'] * self.price_per_sqft_weight +
            factors['unit_density'] * self.unit_density_weight +
            factors['property_size'] * self.size_weight +
            factors['property_type'] * self.property_type_weight
        )
        
        # Generate explanation
        explanation = self._generate_explanation(property, factors, overall_score)
        
        return InvestmentScore(
            property_id=property.id,
            overall_score=round(overall_score, 1),
            factors={k: round(v, 1) for k, v in factors.items()},
            explanation=explanation
        )
    
    def _score_cap_rate(self, cap_rate: float) -> float:
        """Score based on cap rate (0-100). Target is ~8% for good investments."""
        # Convert to percentage
        rate_pct = cap_rate * 100
        
        if rate_pct < 0:
            return 0
        elif rate_pct <= self.target_cap_rate * 100:
            # Below target, score proportionally
            return (rate_pct / (self.target_cap_rate * 100)) * 100
        else:
            # Above target (better return), score up to 100
            # Diminishing returns for very high cap rates
            excess = rate_pct - (self.target_cap_rate * 100)
            return min(100, 100 + (excess * 2))
    
    def _score_price_per_sqft(self, price_per_sqft: float) -> float:
        """Score based on price per square foot (0-100)."""
        # Optimal at target price
        if price_per_sqft <= self.target_price_per_sqft:
            # Lower is better, but diminishing returns
            ratio = price_per_sqft / self.target_price_per_sqft
            return min(100, ratio * 100)
        else:
            # More expensive = lower score
            ratio = self.target_price_per_sqft / price_per_sqft
            return max(0, ratio * 100)
    
    def _score_unit_density(self, bedrooms: int, bathrooms: int, sqft: int) -> float:
        """Score based on rental unit density (beds + baths relative to space)."""
        if sqft == 0:
            return 0
        
        # Calculate beds + baths per 100 sqft
        units_per_100sqft = ((bedrooms + bathrooms) / sqft) * 100
        
        # Target: ~0.35-0.40 units per 100 sqft is efficient
        target_density = 0.35
        if units_per_100sqft == 0:
            return 0
        
        # Score peaks at target, falls off on either side
        ratio = min(units_per_100sqft / target_density, 1.5)  # Cap at 1.5x
        return (ratio / 1.5) * 100 if ratio <= 1.5 else max(0, 100 - ((ratio - 1.5) * 100))
    
    def _score_size(self, sqft: int) -> float:
        """Score based on property size (larger = higher income potential)."""
        if sqft < self.min_sqft:
            return 20  # Very small properties score low
        elif sqft >= self.ideal_sqft:
            return 100  # Ideal size and above = full score
        else:
            # Linear interpolation between min and ideal
            return 20 + ((sqft - self.min_sqft) / (self.ideal_sqft - self.min_sqft)) * 80
    
    def _score_property_type(self, property_type: str) -> float:
        """Score based on property type suitability for rental investment."""
        type_scores = {
            'Apartment': 95,      # Best for rentals (high density)
            'Condo': 90,          # Very good (lower maintenance)
            'Townhouse': 85,      # Good (moderate maintenance)
            'Multi-Family': 95,   # Excellent (multiple units)
            'House': 70,          # Fair (higher maintenance, single unit)
            'Mobile Home': 75,    # Fair
            'Land': 40,           # Poor (no rental income, development risk)
            'Commercial': 60,     # Fair (different investor profile)
        }
        return type_scores.get(property_type, 50)
    
    def _generate_explanation(
        self,
        property: Property,
        factors: Dict[str, float],
        overall_score: float
    ) -> str:
        """Generate a human-readable explanation of the score."""
        rating = self._get_rating(overall_score)
        
        explanation = f"{rating} Investment ({overall_score}/100)\n"
        explanation += f"  Address: {property.address}\n"
        explanation += f"  {property.bedrooms} bed, {property.bathrooms} bath | {property.square_footage} sqft | {property.property_type}\n"
        
        if property.last_sale_price:
            price_per_sqft = property.last_sale_price / property.square_footage if property.square_footage > 0 else 0
            explanation += f"  Last Sale: ${property.last_sale_price:,.0f} (${price_per_sqft:.2f}/sqft)\n"
        
        explanation += f"\nScore Breakdown:\n"
        
        if 'cap_rate' in factors:
            explanation += f"  • Cap Rate: {factors['cap_rate']}/100\n"
        
        explanation += f"  • Affordability (Price/sqft): {factors['price_per_sqft']}/100\n"
        explanation += f"  • Unit Density: {factors['unit_density']}/100\n"
        explanation += f"  • Property Size: {factors['property_size']}/100\n"
        explanation += f"  • Property Type: {factors['property_type']}/100\n"
        
        return explanation
    
    @staticmethod
    def _get_rating(score: float) -> str:
        """Get rating label for score."""
        if score >= 85:
            return "⭐⭐⭐⭐⭐ Excellent"
        elif score >= 70:
            return "⭐⭐⭐⭐ Very Good"
        elif score >= 50:
            return "⭐⭐⭐ Good"
        elif score >= 30:
            return "⭐⭐ Fair"
        else:
            return "⭐ Poor"


def fetch_properties(zip_code: str, limit: int = 20, bedrooms: int = None, bathrooms: int = None, squareFootage: int = None, price: int = None) -> List[Property]:
    """Fetch properties from RentCast API and convert to Property objects."""
    params = {
        'zipCode': zip_code,
        'limit': limit,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'squareFootage': squareFootage,
        'price': price
    }
    response = httpx.get(
        'https://api.rentcast.io/v1/properties',
        headers={'X-Api-Key': api_key, 'Accept': 'application/json'},
        params={k: v for k, v in params.items() if v is not None}
    )
    
    if response.status_code != 200:
        print(f"Error fetching properties: {response.status_code}")
        return []
    
    return [Property.from_api(data) for data in response.json()]


def fetch_rent_estimate(address: str, city: str, state: str) -> Optional[float]:
    """
    Fetch estimated monthly rent for a property from RentCast API.
    
    Returns estimated monthly rent or None if not available.
    """
    try:
        response = httpx.get(
            'https://api.rentcast.io/v1/avm/rent',
            headers={'X-Api-Key': api_key, 'Accept': 'application/json'},
            params={
                'address': address,
                'city': city,
                'state': state
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('monthlyRentEstimate')
    except Exception as e:
        print(f"Error fetching rent estimate: {e}")
    
    return None


def score_properties_in_zipcode(zip_code: str, limit: int = 20, include_rent_estimates: bool = False) -> List[InvestmentScore]:
    """Fetch and score all properties in a zip code.
    
    Args:
        zip_code: Target zip code
        limit: Max properties to fetch
        include_rent_estimates: If True, fetch actual rent estimates from API (slower but more accurate)
    """
    scorer = InvestmentScorer()
    properties = fetch_properties(zip_code, limit=limit)
    
    scores = []
    for prop in properties:
        # Optionally fetch actual rent estimate
        estimated_rent = None
        if include_rent_estimates:
            estimated_rent = fetch_rent_estimate(prop.address.split(',')[0], prop.city, prop.state)
        
        score = scorer.score(prop, estimated_monthly_rent=estimated_rent)
        scores.append(score)
    
    return sorted(scores, key=lambda s: s.overall_score, reverse=True)