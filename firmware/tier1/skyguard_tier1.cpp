#include "skyguard_tier1.h"
#include <math.h>

#define MAGNUS_A 17.625f
#define MAGNUS_B 243.04f

static float calculate_dew_point(float temp, float humi) {
    float rh_clamped = humi;
    if (rh_clamped < 0.01f) rh_clamped = 0.01f;
    if (rh_clamped > 100.0f) rh_clamped = 100.0f;

    float alpha = logf(rh_clamped / 100.0f) + (MAGNUS_A * temp) / (MAGNUS_B + temp);
    float denom = MAGNUS_A - alpha;
    if (fabsf(denom) < 1e-7f) denom = 1e-7f;
    return (MAGNUS_B * alpha) / denom;
}

void skyguard_tier1_init(skyguard_tier1_context_t *ctx) {
    if (!ctx) return;
    ctx->temp_min = -40.0f;
    ctx->temp_max = 55.0f;
    ctx->pres_min = 500.0f;
    ctx->pres_max = 1080.0f;
    ctx->humi_min = 0.0f;
    ctx->humi_max = 100.0f;
    ctx->max_step_temp = 6.0f;
    ctx->max_step_pres = 5.0f;
    ctx->max_step_humi = 30.0f;
    ctx->persistence_limit = 6;

    ctx->prev_temp = 0.0f;
    ctx->prev_pres = 0.0f;
    ctx->prev_humi = 0.0f;
    ctx->has_prev = false;
    ctx->temp_persist_count = 0;
    ctx->pres_persist_count = 0;
    ctx->humi_persist_count = 0;
}

tier1_result_t skyguard_tier1_evaluate(
    skyguard_tier1_context_t *ctx,
    float temp,
    float pres,
    float humi,
    bool is_valid_reading
) {
    tier1_result_t res;
    res.status = QC_PASS;
    res.rules_fired_mask = 0;
    res.dew_point = 0.0f;
    res.dp_depression = 0.0f;

    if (!ctx) return res;

    // 1. Missing data check
    if (!is_valid_reading || isnan(temp) || isnan(pres) || isnan(humi)) {
        res.rules_fired_mask |= RULE_FLAG_MISSING;
        res.status = QC_SUSPECT;
        return res;
    }

    // 2. Range check
    if (temp < ctx->temp_min || temp > ctx->temp_max ||
        pres < ctx->pres_min || pres > ctx->pres_max ||
        humi < ctx->humi_min || humi > ctx->humi_max) {
        res.rules_fired_mask |= RULE_FLAG_RANGE;
        res.status = QC_FAIL;
    }

    // 3. Dew point thermodynamic invariant check
    res.dew_point = calculate_dew_point(temp, humi);
    res.dp_depression = temp - res.dew_point;
    if (res.dp_depression < -0.1f) {
        res.rules_fired_mask |= RULE_FLAG_DEW_POINT;
        res.status = QC_FAIL;
    }

    // 4. Persistence & Step checks (requires history)
    if (ctx->has_prev) {
        float dt = fabsf(temp - ctx->prev_temp);
        float dp = fabsf(pres - ctx->prev_pres);
        float dh = fabsf(humi - ctx->prev_humi);

        // Step check
        if (dt > ctx->max_step_temp || dp > ctx->max_step_pres || dh > ctx->max_step_humi) {
            res.rules_fired_mask |= RULE_FLAG_STEP;
            if (res.status != QC_FAIL) res.status = QC_SUSPECT;
        }

        // Persistence check
        if (dt < 0.05f) ctx->temp_persist_count++; else ctx->temp_persist_count = 0;
        if (dp < 0.05f) ctx->pres_persist_count++; else ctx->pres_persist_count = 0;
        if (dh < 0.05f) ctx->humi_persist_count++; else ctx->humi_persist_count = 0;

        if (ctx->temp_persist_count >= ctx->persistence_limit ||
            ctx->pres_persist_count >= ctx->persistence_limit ||
            ctx->humi_persist_count >= ctx->persistence_limit) {
            res.rules_fired_mask |= RULE_FLAG_PERSISTENCE;
            res.status = QC_FAIL;
        }
    }

    // Update state
    ctx->prev_temp = temp;
    ctx->prev_pres = pres;
    ctx->prev_humi = humi;
    ctx->has_prev = true;

    return res;
}
