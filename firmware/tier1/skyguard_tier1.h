#ifndef SKYGUARD_TIER1_H
#define SKYGUARD_TIER1_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Status code definitions
typedef enum {
    QC_PASS = 0,
    QC_SUSPECT = 1,
    QC_FAIL = 2
} qc_status_t;

// Bitmask flags for fired rules
#define RULE_FLAG_RANGE        (1 << 0)
#define RULE_FLAG_STEP         (1 << 1)
#define RULE_FLAG_PERSISTENCE  (1 << 2)
#define RULE_FLAG_DEW_POINT    (1 << 3)
#define RULE_FLAG_MISSING      (1 << 4)

// State container for running on ESP32 without dynamic allocation
typedef struct {
    // Limits
    float temp_min;
    float temp_max;
    float pres_min;
    float pres_max;
    float humi_min;
    float humi_max;
    float max_step_temp;
    float max_step_pres;
    float max_step_humi;
    uint8_t persistence_limit;

    // Stateful tracking
    float prev_temp;
    float prev_pres;
    float prev_humi;
    bool has_prev;
    uint8_t temp_persist_count;
    uint8_t pres_persist_count;
    uint8_t humi_persist_count;
} skyguard_tier1_context_t;

typedef struct {
    qc_status_t status;
    uint16_t rules_fired_mask;
    float dew_point;
    float dp_depression;
} tier1_result_t;

void skyguard_tier1_init(skyguard_tier1_context_t *ctx);
tier1_result_t skyguard_tier1_evaluate(
    skyguard_tier1_context_t *ctx,
    float temp,
    float pres,
    float humi,
    bool is_valid_reading
);

#ifdef __cplusplus
}
#endif

#endif // SKYGUARD_TIER1_H
