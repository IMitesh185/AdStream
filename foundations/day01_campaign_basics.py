'''
    Create a Python script 
    storing advertiser ID, campaign name, daily budget in integer 
    currency minor units (micros/cents—explain why vs float), 
    impressions, clicks, and cost; 
    compute CTR, CPC, CPM, and remaining budget; 
    print a formatted summary.
'''
def main():
    advertiser_id = input("Enter advertiser ID: ")
    campaign_name = input("Enter campaign name: ")
    campaign_id = input("Enter campaign ID: ")
    daily_budget_micros = int(input("Enter daily budget in minor currency units: "))
    impressions = int(input("Enter number of impressions: "))
    clicks = int(input("Enter number of clicks: "))
    cost = int(input("Enter cost in minor currency units: "))
    is_active = bool(int(input("Is the campaign active? (1 for Yes, 0 for No): ")))
    
    ctr = (clicks / impressions) if impressions > 0 else 0
    cpc = (cost // clicks) if clicks > 0 else 0
    cpm = ((cost * 1000) // impressions) if impressions > 0 else 0
    remaining_budget_usd = (daily_budget_micros - cost) / 1000000

    print(f"Campaign Summary for {campaign_name}:")
    print(f"Advertiser ID: {advertiser_id}")
    print(f"Campaign ID: {campaign_id}")
    print(f"Daily Budget: {daily_budget_micros / 1000000:.2f}")
    print(f"Impressions: {impressions}")
    print(f"Clicks: {clicks}")
    print(f"Cost: {cost / 1000000:.2f}")
    print(f"CTR: {ctr:.2%}")
    print(f"CPC: {cpc / 1000000:.2f}")
    print(f"CPM: {cpm / 1000000:.2f}")
    print(f"Remaining Budget: {remaining_budget_usd:.2f}")
    print(f"Campaign Active: {'Yes' if is_active else 'No'}")

if __name__ == "__main__":
    main()