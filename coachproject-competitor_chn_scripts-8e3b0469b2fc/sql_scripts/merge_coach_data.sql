CREATE TEMP TABLE tmp_cte as
WITH coh_sales_data AS (
    SELECT
        substring(a.cal_date,1,4)::int as year,
        substring(a.cal_date,6,2)::int as month,
        b.door_code,
        CASE a.CHNL_CODE
            WHEN 'CAFP' THEN 'Retail'
            WHEN 'CAFS' THEN 'Outlet'
        END as store_category,
        round(sum(NET_SALES_AMT_LCL)/1000) as NET_SALES_AMT_LCL
    FROM {env}_crm.cdlcrm.VW_RPT_SALES_CURR_EXP_MST2 a
    LEFT JOIN {env}_crm.cdlcrm.cdl_mstr_location b ON a.location_key=b.location_id
    WHERE a.chnl_code in ('CAFP','CAFS')
    AND version_code='Act'
    AND TO_CURR_CODE='AOP Plan Rate'
    AND RATE_YEAR_MODE='TY'
    AND product_type='ZFG'
    AND cal_key=1
    AND Country_code in ('CN')
    AND SAP_DISTRB_CHNL_KEY <> 'EC'
    --and version_reg_clr = 'Act - Reg'
    GROUP BY 1,2,3,4
),
coh_sales_data_ty_vs_ly AS (
    SELECT
        curr.year,
        curr.month,
        curr.door_code,
        curr.store_category,
        curr.NET_SALES_AMT_LCL,
        CASE
            WHEN curr.NET_SALES_AMT_LCL > 0
                AND COALESCE(prev.NET_SALES_AMT_LCL, 0) > 0
            THEN 'Y'
            ELSE 'N'
        END as comp
    FROM coh_sales_data curr
    LEFT JOIN coh_sales_data prev
    ON curr.door_code = prev.door_code
    AND curr.year = prev.year + 1
    AND curr.month = prev.month
)
,coh_sales_data_final as (
SELECT
year
,month
,null as manager_name
,door_code as store_code
,null as store_name
,'Coach' as brand_name
,NET_SALES_AMT_LCL as amount
,comp
,null as comment
,store_category
FROM coh_sales_data_ty_vs_ly)
,coh_pure_sales_data_pre as (
    select cal_date,
           location_key,
           chnl_code,
           version_code,
           TO_CURR_CODE,
           RATE_YEAR_MODE,
           product_type,
           cal_key,
           SAP_DISTRB_CHNL_KEY,
           sum(NET_SALES_AMT_LCL) as NET_SALES_AMT_LCL
    from {env}_crm.cdlcrm.VW_RPT_SALES_CURR_EXP_MST2
    group by 1,2,3,4,5,6,7,8,9
)
,coh_pure_sales_data_base AS (
    SELECT
        substring(a.cal_date,1,4)::int as year,
        substring(a.cal_date,6,2)::int as month,
        b.door_code,
        --'Retail' as store_category,
        (a.NET_SALES_AMT_LCL-coalesce(c.clr_pce_ss_ttl_amt_lcl,0)) as NET_SALES_AMT_LCL
    FROM coh_pure_sales_data_pre a
    LEFT JOIN {env}_crm.cdlcrm.cdl_mstr_location b ON a.location_key=b.location_id
    left join {env}_ind360.landing.cohpure_clr_sku_list c on c.store_code = b.door_code and a.cal_date = c.cal_date
    WHERE a.chnl_code in ('CAFP')
    AND a.version_code='Act'
    AND TO_CURR_CODE='AOP Plan Rate'
    AND RATE_YEAR_MODE='TY'
    AND a.product_type='ZFG'
    AND cal_key=1
    AND b.country_code in ('CN')
    AND a.SAP_DISTRB_CHNL_KEY <> 'EC'
)
,coh_pure_sales_data as (
select
year,
month,
door_code,
'Retail' as store_category,
round(sum(NET_SALES_AMT_LCL)/1000) as NET_SALES_AMT_LCL
from coh_pure_sales_data_base
group by
1,2,3,4
)
,coh_pure_sales_data_ty_vs_ly AS (
    SELECT
        curr.year,
        curr.month,
        curr.door_code,
        curr.store_category,
        curr.NET_SALES_AMT_LCL,
        CASE
            WHEN curr.NET_SALES_AMT_LCL > 0
                AND COALESCE(prev.NET_SALES_AMT_LCL, 0) > 0
            THEN 'Y'
            ELSE 'N'
        END as comp
    FROM coh_pure_sales_data curr
    LEFT JOIN coh_pure_sales_data prev
    ON curr.door_code = prev.door_code
    AND curr.year = prev.year + 1
    AND curr.month = prev.month
)
,coh_pure_sales_data_final as (
SELECT
 year
,month
,null as manager_name
,door_code as store_code
,null as store_name
,'Coach (pure)' as brand_name
,NET_SALES_AMT_LCL as amount
,comp
,null as comment
,store_category
FROM coh_pure_sales_data_ty_vs_ly)
select *
from coh_sales_data_final
where year>=2024
union all
select *
from coh_pure_sales_data_final
where year>=2024;
 
DELETE FROM landing.inhouse_sales_data_collection
USING tmp_cte s
WHERE  landing.inhouse_sales_data_collection.year = s.year
AND  landing.inhouse_sales_data_collection.month = s.month
AND  landing.inhouse_sales_data_collection.store_code = s.store_code
AND  landing.inhouse_sales_data_collection.brand_name = s.brand_name;
 
INSERT INTO  landing.inhouse_sales_data_collection
SELECT * FROM tmp_cte;
 
DROP TABLE tmp_cte;