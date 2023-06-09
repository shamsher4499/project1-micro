USER_TYPE = (
    ('BORROWER', 'BORROWER'),
    ('LENDER', 'LENDER'),
    ('BOTH', 'BOTH')
)

QUERY_STATUS = (
    ('PENDING', 'PENDING'),
    ('RESOLVED', 'RESOLVED'),
    # ('VIEW', 'VIEW'),
)

AMOUNT_STATUS = (
    ('CREDIT', 'CREDIT'),
    ('DEBIT', 'DEBIT'),
)

REQUEST_TYPE = (
    ('DIRECT', 'DIRECT'),
    ('BID', 'BID'),
)

WALLET_STATUS = (
    ('HOLD', 'HOLD'),
    ('ACTIVE', 'ACTIVE'),
    ('BLOCKED', 'BLOCKED'),
)

COMMISSION_TYPE = (
    ('PERCENTAGE', 'PERCENTAGE'),
    ('FIXED_PRICE', 'FIXED_PRICE'),
)

INTERVAL_TYPE = (
    ('MONTHLY', 'MONTHLY'),
    ('ANNUALLY', 'ANNUALLY'),
)

RECURRING_TYPE = (
    ('AUTO', 'AUTO'),
    ('MANUALLY', 'MANUALLY'),
)

TIER_TYPE = (
    ('TIER 1', 'TIER 1'),
    ('TIER 2', 'TIER 2'),
    ('TIER 3', 'TIER 3'),
)

BUSINESS_TYPE = (
    ('SOLE PROPRIETORSHIP', 'SOLE PROPRIETORSHIP'),
    ('PARTNERSHIPS', 'PARTNERSHIPS'),
    ('LIMITED LIABILITY COMPANY', 'LIMITED LIABILITY COMPANY'),
    ('CORPORATION C CORP', 'CORPORATION C CORP'),
    ('CORPORATION S CORP', 'CORPORATION S CORP'),
    ('CORPORATION B CORP', 'CORPORATION B CORP'),
    ('CORPORATION NONPROFIT', 'CORPORATION NONPROFIT'),
)

CATEGORY_TYPE = (
    ('NEW', 'NEW'),
    ('PRO', 'PRO'),
    ('PREMIUM', 'PREMIUM'),
)

LOAN_TYPE = (
    ('CASH', 'CASH'),
    ('PRODUCT', 'PRODUCT'),
)