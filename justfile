# justfile for toolbox

# Default task: runs daily schedule for today
default:
    CLOCKIFY_ACTION="daily" python timerz/clockify.py

# Remove night entries for the last two weeks
remove_nights:
    CLOCKIFY_ACTION="remove_nights" python timerz/clockify.py

# Autofill a specific date (YYYY-MM-DD)
autofill DATE:
    CLOCKIFY_ACTION="autofill_specific_date" CLOCKIFY_DATE="{{DATE}}" python timerz/clockify.py

# Autofill Monday to Friday for the current week
autofill_week:
    #!/usr/bin/env bash
    set -e
    echo "Autofilling work hours for the current week (Monday to Friday)"
    # Calculate Monday of the current week
    # %u gives day of week (1..7); 1 is Monday.
    # So, subtract (day_of_week - 1) days from current date to get to Monday.
    DAYS_TO_SUBTRACT_FOR_MONDAY=$(( $(date +%u) - 1 ))
    MONDAY_OF_CURRENT_WEEK=$(date -d "-${DAYS_TO_SUBTRACT_FOR_MONDAY} days" +%Y-%m-%d)

    for i in {0..4}; do
        TARGET_DATE=$(date -d "${MONDAY_OF_CURRENT_WEEK} +$i days" +%Y-%m-%d)
        echo "Autofilling for $TARGET_DATE"
        just autofill $TARGET_DATE
    done

# Autofill a range of dates (YYYY-MM-DD YYYY-MM-DD)
autofill_range START_DATE END_DATE:
    #!/usr/bin/env bash
    set -e
    echo "Autofilling work hours from {{START_DATE}} to {{END_DATE}}"
    CURRENT_DATE={{START_DATE}}
    while [[ "$CURRENT_DATE" < "$END_DATE" || "$CURRENT_DATE" == "$END_DATE" ]]; do
        # Check if it's a weekday (1-5, where 1 is Monday)
        DAY_OF_WEEK=$(date -d "$CURRENT_DATE" +%u)
        if (( DAY_OF_WEEK >= 1 && DAY_OF_WEEK <= 5 )); then
            echo "Autofilling for $CURRENT_DATE"
            just autofill $CURRENT_DATE
        else
            echo "Skipping weekend: $CURRENT_DATE"
        fi
        CURRENT_DATE=$(date -d "$CURRENT_DATE + 1 day" +%Y-%m-%d)
    done

# Run morning schedule for today
run_morning:
    CLOCKIFY_ACTION="daily" python timerz/clockify.py # Assuming daily includes morning schedule

# Add HPFO task for today
run_hpfo:
    CLOCKIFY_ACTION="daily" python timerz/clockify.py # Assuming daily includes HPFO task
