#!/bin/bash

# Traefik Memory Monitoring Script
# Tracks memory usage over time and writes to file

NAMESPACE="explorer-beta"
OUTPUT_FILE="traefik_memory_usage.log"
INTERVAL=30  # seconds between checks

echo "Starting Traefik memory monitoring..."
echo "Namespace: $NAMESPACE"
echo "Output file: $OUTPUT_FILE"
echo "Check interval: ${INTERVAL}s"
echo ""

# Create header in output file
echo "timestamp,pod_name,cpu_cores,memory_bytes,memory_mi,memory_limit_mi,memory_usage_percent" > "$OUTPUT_FILE"

# Function to get pod metrics
get_pod_metrics() {
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l k8s-app=traefik -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        echo "$(date): No Traefik pod found" | tee -a "$OUTPUT_FILE"
        return 1
    fi
    
    # Get resource usage
    local metrics=$(kubectl top pod "$pod_name" -n "$NAMESPACE" --no-headers 2>/dev/null)
    
    if [ -z "$metrics" ]; then
        echo "$(date): Unable to get metrics for pod $pod_name" | tee -a "$OUTPUT_FILE"
        return 1
    fi
    
    # Parse metrics
    local cpu=$(echo "$metrics" | awk '{print $2}')
    local memory=$(echo "$metrics" | awk '{print $3}')
    
    # Get memory limit from pod spec
    local memory_limit=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.spec.containers[0].resources.limits.memory}' 2>/dev/null)
    
    # Convert memory to bytes and Mi for calculations
    local memory_bytes=""
    local memory_mi=""
    
    if [[ "$memory" =~ ([0-9]+)Mi$ ]]; then
        memory_mi="${BASH_REMATCH[1]}"
        memory_bytes=$((memory_mi * 1024 * 1024))
    elif [[ "$memory" =~ ([0-9]+)Ki$ ]]; then
        local memory_ki="${BASH_REMATCH[1]}"
        memory_mi=$((memory_ki / 1024))
        memory_bytes=$((memory_ki * 1024))
    fi
    
    # Convert limit to Mi
    local limit_mi=""
    if [[ "$memory_limit" =~ ([0-9]+)Mi$ ]]; then
        limit_mi="${BASH_REMATCH[1]}"
    fi
    
    # Calculate usage percentage
    local usage_percent=""
    if [ -n "$memory_mi" ] && [ -n "$limit_mi" ] && [ "$limit_mi" -gt 0 ]; then
        usage_percent=$(echo "scale=2; $memory_mi * 100 / $limit_mi" | bc)
    fi
    
    # Log the data
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_line="$timestamp,$pod_name,$cpu,$memory_bytes,${memory_mi}Mi,${limit_mi}Mi,${usage_percent}%"
    
    echo "$log_line" | tee -a "$OUTPUT_FILE"
    
    # Also display human-readable format
    echo "Pod: $pod_name | Memory: ${memory_mi}Mi/${limit_mi}Mi (${usage_percent}%) | CPU: $cpu"
}

# Trap to handle Ctrl+C
trap 'echo ""; echo "Monitoring stopped. Results saved to $OUTPUT_FILE"; exit 0' INT

echo "Starting monitoring (Press Ctrl+C to stop)..."
echo ""

# Main monitoring loop
while true; do
    get_pod_metrics
    sleep "$INTERVAL"
done