import matplotlib.pyplot as plt

# Function to annotate horizontal bars with percentage text
def annotate_bar(ax, y, values, text_color="#444444"):
    left = 0
    for v in values:
        ax.text(
            left + v / 2,  # Place text at the center of the segment
            y,
            f"{v:.1f}%",
            ha="center",
            va="center",
            fontsize=9,
            color=text_color,
        )
        left += v  # Move to the next segment

if __name__ == "__main__":

    # Data (percentages)
    phases = ["Test Scenario Generator", "Test Scenario Executor", "Bug Detector"]

    time_pct = [6.9, 40.8, 52.3]  # Execution time breakdown
    cost_pct = [4.1, 59.3, 36.7]  # Monetary cost breakdown

    # Colors matching the Venn diagram style
    colors = ["#E3E3E3", "#F6D6DE", "#E9A9BC"]

    fig, ax = plt.subplots(figsize=(10, 2.1))

    # Draw Execution Time bar
    left = 0
    for pct, color in zip(time_pct, colors):
        ax.barh(
            "Time",  # Horizontal bar label
            pct,
            left=left,
            color=color,
            linewidth=0.6,
        )
        left += pct

    # Draw Monetary Cost bar
    left = 0
    for pct, color in zip(cost_pct, colors):
        ax.barh(
            "Cost",  # Horizontal bar label
            pct,
            left=left,
            color=color,
            linewidth=0.6,
        )
        left += pct

    # Axis formatting
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentage (%)")
    ax.set_ylabel("")  # Hide y-axis label
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    # Legend (order and colors match the figure)
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=c) for c in colors]
    ax.legend(
        handles,
        phases,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.32),  # Position above the plot
        ncol=3,
        frameon=False,
    )

    # Add text annotations after all bars are drawn
    annotate_bar(ax, "Time", time_pct)
    annotate_bar(ax, "Cost", cost_pct)

    plt.tight_layout()
    plt.savefig("overhead_breakdown.pdf")
    plt.show()
