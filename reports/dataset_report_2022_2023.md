# Dataset Report: 2022-2023 (raw marketplace)

Shape: (52193, 26)

## Columns & dtypes

ad_title                object
ad_description          object
details                 object
slug                    object
title                   object
type                    object
price                   object
timestamp               object
posted_date             object
deactivation_date       object
category                object
parent_category         object
location                object
geo_region              object
area                    object
is_delivery_free          bool
is_doorstep_delivery      bool
is_dsd_applicable         bool
is_member               object
is_authorized_dealer    object
is_featured_member      object
is_verified               bool
membership_level        object
member_since            object
properties              object
user                    object


## Missing ratio (top 15)

member_since            0.129040
is_authorized_dealer    0.026345
is_featured_member      0.026345
is_member               0.026345
price                   0.005805
details                 0.005805
deactivation_date       0.000057
posted_date             0.000057
timestamp               0.000057
ad_title                0.000000
title                   0.000000
slug                    0.000000
type                    0.000000
ad_description          0.000000
category                0.000000


## Irrelevant / Non-predictive Columns (Preliminary)

- Platform / logistics fields (not related to property value)
  - is_delivery_free
  - is_doorstep_delivery
  - is_dsd_applicable
  - category, parent_category

- Seller / membership metadata (may introduce platform bias)
  - membership_level
  - is_featured_member
  - is_authorized_dealer
  - is_member
  - is_verified
  - member_since

**Note:** These columns are preserved in raw data but will be excluded or carefully evaluated in Step 2.


## Location Fields (To Be Enhanced Later)

- area, district, location: categorical, coarse-grained
- address: raw string (available mainly in 2025 data)
**Planned:** Convert to latitude/longitude using geocoding in later steps to enable spatial features and GNN modeling.


## Sample rows

                                          ad_title                                                                                                                                                                          ad_description                    details                                                      slug                                    title      type           price        timestamp                posted_date         deactivation_date         category parent_category       location geo_region                             area  is_delivery_free  is_doorstep_delivery  is_dsd_applicable is_member is_authorized_dealer is_featured_member  is_verified membership_level   member_since                                                                                                                                   properties                                                              user
0  Semi Luxury House for Sale in Kadawatha | ikman  Semi Luxury House in Kadawatha\nLocated at Pinthaliya Road\n\nJest about 100 meters to Kandy Road\n\nHouse consisting of 2 levels with roof terrace\n\nâ¼ Ground Floor (1658 Sq ft...  Bedrooms: 5, Bathrooms: 4  semi-luxury-house-for-sale-in-kadawatha-for-sale-gampaha  Semi Luxury House for Sale in Kadawatha  for_sale   Rs 55,000,000   30 Jan 8:54 am  2023-01-30T08:54:09+05:30  2021-10-03T08:33:36.000Z  Houses For Sale        Property      Kadawatha      LK-12  {'id': 1577, 'name': 'Gampaha'}             False                 False              False      True                False              False         True          premium    August 2016      {'Address': 'Pinthaliya Road, Kadawatha', 'Bedrooms': '5', 'Bathrooms': '4', 'House size': '3,000.0 sqft', 'Land size': '27.5 perches'}  147c45b684bfeae3e3ffb0397b126d4e67392ad600e254948cbee5cb32f326bf
1     Two Story House for Sale in Dehiwela | ikman        Kadawatha Road Dehiwala \n4 bedrooms 4 bathrooms pantry and wet kitchen maid room and bathroom small store room fully A/C and full solar power\n2 Car park Available\nPrice :...  Bedrooms: 4, Bathrooms: 4   two-story-house-for-sale-in-dehiwela-for-sale-colombo-6     Two Story House for Sale in Dehiwela  for_sale   Rs 80,000,000  14 Feb 10:31 pm  2023-02-14T22:31:10+05:30  2022-01-30T17:38:24.000Z  Houses For Sale        Property       Dehiwala      LK-11  {'id': 1506, 'name': 'Colombo'}             False                 False              False      True                False              False         True          premium  February 2021                  {'Address': 'kadawatha Road', 'Bedrooms': '4', 'Bathrooms': '4', 'House size': '3,000.0 sqft', 'Land size': '8.75 perches'}  765b8447b8c0b5fd5027da030129879e06ca0e744dc8da21b44f8b7f29ff7305
2          House for Sale in Mount Lavinia | ikman   A Two-story British style house for sale in Mount Lavinia\nLocated Off temples Road\n\nPeaceful surroundings & Exclusive Neighborhood\n\nâ¦ First Floor \nOne bed room and a comm...  Bedrooms: 4, Bathrooms: 2      house-for-sale-in-mount-lavinia-for-sale-colombo-745          House for Sale in Mount Lavinia  for_sale  Rs 125,000,000   30 Jan 8:54 am  2023-01-30T08:54:39+05:30  2022-07-30T10:15:29.000Z  Houses For Sale        Property  Mount Lavinia      LK-11  {'id': 1506, 'name': 'Colombo'}             False                 False              False      True                False              False         True          premium    August 2016  {'Address': 'Off Temple Road, Mount Lavinia', 'Bedrooms': '4', 'Bathrooms': '2', 'House size': '5,600.0 sqft', 'Land size': '20.0 perches'}  147c45b684bfeae3e3ffb0397b126d4e67392ad600e254948cbee5cb32f326bf