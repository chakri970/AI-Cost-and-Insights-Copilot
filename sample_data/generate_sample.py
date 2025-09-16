import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

os.makedirs("sample_data", exist_ok=True)


def gen_months(n=6, start='2025-04-01'):
    s = pd.to_datetime(start)
    return [(s + pd.DateOffset(months=i)).strftime('%Y-%m-01') for i in range(n)]


def gen_data(n_resources=200, months=6):
    resources = []
    for i in range(n_resources):
        rid = f"res-{i:04d}"
        env = np.random.choice(['prod', 'staging', 'dev'])
        owner = np.random.choice(['alice', 'bob', 'carol', None], p=[
                                 0.35, 0.35, 0.25, 0.05])
        tags = {
            'app': f'app-{np.random.randint(1, 50)}', 'size': np.random.choice(['S', 'M', 'L'])}
        resources.append({'resource_id': rid, 'owner': owner,
                         'env': env, 'tags_json': json.dumps(tags)})
    billing = []
    months_list = gen_months(months)
    for m in months_list:
        for r in resources:
            base = np.random.uniform(5, 300)
            season_factor = 1 + np.random.normal(0, 0.2)
            cost = round(base*season_factor, 2)
            usage_qty = round(np.random.uniform(0.0, 50.0), 3)
            unit_cost = round(cost / max(usage_qty, 0.01), 3)
            billing.append({
                'invoice_month': m, 'account_id': 'acct-1', 'subscription': 'sub-1',
                'service': np.random.choice(['Compute', 'Storage', 'DB', 'Networking']),
                'resource_group': np.random.choice(['rg-prod', 'rg-dev', 'rg-staging']),
                'resource_id': r['resource_id'],
                'region': np.random.choice(['eastus', 'westeurope', 'southeastasia']),
                'usage_qty': usage_qty, 'unit_cost': unit_cost, 'cost': cost,
                'raw_json': '{}'
            })
    df_b = pd.DataFrame(billing)
    df_r = pd.DataFrame(resources)
    df_b.to_csv('sample_data/billing.csv', index=False)
    df_r.to_csv('sample_data/resources.csv', index=False)
    print("Written sample_data/billing.csv and sample_data/resources.csv")


if __name__ == '__main__':
    gen_data(500, 6)
