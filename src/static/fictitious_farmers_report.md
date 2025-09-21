# Fictitious Farmers Dataset Report

**Generated:** September 16, 2025  
**Total Records:** 2,500 farmers  
**Purpose:** Testing and demonstration of AgSense ERP system scalability

## Overview

This report provides a comprehensive analysis of the 2,500 fictitious farmer records generated for the AgSense ERP system. All records are clearly marked as "FICTITIOUS DATA" to distinguish them from real farmer information.

## Dataset Characteristics

### Geographic Distribution
The farmers are distributed across major agricultural regions in the Philippines:
- **Nueva Ecija** - Rice and corn farming regions
- **Pangasinan** - Major rice production area
- **Iloilo & Negros Occidental** - Sugar and rice production
- **Camarines Sur** - Rice and coconut farming
- **Isabela & Cagayan** - Corn and rice production
- **Bukidnon & South Cotabato** - Diverse crop production

### Crop Distribution
The dataset includes realistic crop diversity reflecting Philippine agriculture:

| Crop | Number of Farmers | Percentage |
|------|------------------|------------|
| Rice | 332 | 13.3% |
| Corn | 346 | 13.8% |
| Sugarcane | 345 | 13.8% |
| Banana | 168 | 6.7% |
| Cacao | 174 | 7.0% |
| Cassava | 173 | 6.9% |
| Coconut | 161 | 6.4% |
| Coffee | 165 | 6.6% |
| Mango | 151 | 6.0% |
| Peanut | 173 | 6.9% |
| Soybean | 171 | 6.8% |
| Sweet Potato | 141 | 5.6% |

### Loan Status Distribution
The farmers have varied loan statuses reflecting real-world scenarios:

| Status | Number of Farmers | Percentage |
|--------|------------------|------------|
| Pending | 2,338 | 93.5% |
| Approved | 45 | 1.8% |
| Under Review | 31 | 1.2% |
| Disbursed | 34 | 1.4% |
| Partially Disbursed | 28 | 1.1% |
| Completed | 24 | 1.0% |

### Financial Analysis
**Loan Amount Statistics:**
- **Average Loan:** ₱8,312.23
- **Minimum Loan:** ₱0.00 (new farmers or those not requiring loans)
- **Maximum Loan:** ₱495,147.80 (large-scale sugarcane operations)

### Farm Size Distribution
- **Range:** 0.5 to 5.0 hectares
- **Target:** Small to medium-scale farmers (typical CARD MRI demographic)
- **Realistic:** Reflects actual farm sizes in the Philippines

### AgScore Distribution
Farmers are distributed across AgScore ranges:
- **Excellent (850-950):** 10% of farmers
- **Very Good (750-849):** 20% of farmers  
- **Good (650-749):** 35% of farmers
- **Fair (550-649):** 25% of farmers
- **Poor (400-549):** 8% of farmers
- **New (500-600):** 2% of farmers

## Data Quality Features

### Realistic Names
- Uses authentic Filipino first and last names
- Reflects cultural diversity across regions

### Contact Information
- Philippine mobile number formats (0917, 0918, etc.)
- Unique email addresses with ".fictitious" identifier
- Complete addresses with barangay, municipality, and province

### Agricultural Accuracy
- Seasonal crop cycles (wet season, dry season, year-round)
- Realistic fertilizer types and application rates
- Accurate cost calculations based on Philippine market prices

### Temporal Data
- Registration dates spanning the last 2 years
- Recent activity dates showing active engagement
- Realistic farming cycles and seasons

## System Testing Capabilities

This dataset enables comprehensive testing of:

1. **Scalability:** 2,500 records test system performance at scale
2. **Search & Filtering:** Diverse data for testing search functionality
3. **Reporting:** Rich dataset for analytics and financial reports
4. **User Interface:** Large dataset tests pagination and loading
5. **Data Export:** Bulk export functionality testing
6. **Role-Based Access:** Different user roles accessing varied data

## Identification Markers

All fictitious records include:
- **Email Suffix:** ".fictitious" in all email addresses
- **Notes Field:** "FICTITIOUS DATA - Generated for testing purposes"
- **Crop Details:** Detailed crop and fertilizer information in notes
- **Clear Labeling:** Easy identification and filtering of test data

## Usage Recommendations

1. **Development Testing:** Use for feature development and bug testing
2. **Performance Testing:** Validate system performance with large datasets
3. **User Training:** Provide realistic data for user training sessions
4. **Demo Purposes:** Showcase system capabilities to stakeholders
5. **Load Testing:** Test system behavior under realistic data loads

## Data Cleanup

When transitioning to production:
1. Filter by notes containing "FICTITIOUS DATA"
2. Delete all test records before live deployment
3. Verify no fictitious data remains in production database
4. Implement data validation to prevent similar test data entry

This comprehensive dataset provides a robust foundation for testing the AgSense ERP system's capabilities while maintaining clear separation from real farmer data.

