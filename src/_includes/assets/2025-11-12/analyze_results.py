import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import argparse

# Set plot style
sns.set_theme(style="whitegrid")

def load_results(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: Could not find {filename}")
        return []

def analyze(results_file):
    raw_data = load_results(results_file)
    if not raw_data: return

    # 1. Convert JSON to DataFrame for easy math
    rows = []
    for item in raw_data:
        rows.append({
            'id': item['id'],
            'type': item['type'],
            'Score A': item['method_a']['score'],
            'Score B': item['method_b']['score'],
            'Score C': item['method_c']['score'],
            'Delta B': item['method_b']['score'] - item['method_a']['score'],
            'Delta C': item['method_c']['score'] - item['method_a']['score'],
        })
    
    df = pd.DataFrame(rows)

    # --- METRIC 1: Executive Summary ---
    print("="*50)
    print("       EVALUATION METRICS REPORT       ")
    print("="*50)
    print(f"Total Questions Evaluated: {len(df)}")
    print(f"Overall Average - Method A (Image Only):  {df['Score A'].mean():.2%}")
    print(f"Overall Average - Method B (Image+JSON):  {df['Score B'].mean():.2%}")
    print(f"Overall Average - Method C (JSON Only):  {df['Score C'].mean():.2%}")
    
    improvement = df['Score B'].mean() - df['Score A'].mean()
    print(f"Net Improvement Method B: {'+' if improvement > 0 else ''}{improvement:.2%}")
    
    improvement = df['Score C'].mean() - df['Score A'].mean()
    print(f"Net Improvement Method C: {'+' if improvement > 0 else ''}{improvement:.2%}")
    
    # --- METRIC 2: Win/Loss Analysis ---
    # Win: B is better than A by at least 5%
    # Loss: A is better than B by at least 5%
    # Tie: Within 5% of each other
    threshold = 0.015
    wins = df[df['Delta B'] > threshold]
    losses = df[df['Delta B'] < -threshold]
    ties = df[(df['Delta B'] >= -threshold) & (df['Delta B'] <= threshold)]
    
    print("-" * 30)
    print("Head-to-Head Performance (Threshold: 1.5%)")
    print(f"Method B Wins: {len(wins)} ({len(wins)/len(df):.1%})")
    print(f"Method B Loses: {len(losses)} ({len(losses)/len(df):.1%})")
    print(f"Ties:           {len(ties)} ({len(ties)/len(df):.1%})")

    wins = df[df['Delta C'] > threshold]
    losses = df[df['Delta C'] < -threshold]
    ties = df[(df['Delta C'] >= -threshold) & (df['Delta C'] <= threshold)]
    
    print("-" * 30)
    print(f"Method C Wins: {len(wins)} ({len(wins)/len(df):.1%})")
    print(f"Method C Loses: {len(losses)} ({len(losses)/len(df):.1%})")
    print(f"Ties:           {len(ties)} ({len(ties)/len(df):.1%})")

    # --- METRIC 3: The "Save" Rate ---
    # How often did Method A fail (score < 50%) and Method B succeed (score > 80%)?
    saves = df[(df['Score A'] < 0.50) & (df['Score B'] > 0.80)]
    print("-" * 30)
    if not saves.empty:
        print("Examples of fixed errors:")
        for i, row in saves.head(5).iterrows():
            print(f" - ID: {row['id']} ({row['type']}) | A: {row['Score A']:.2f} -> B: {row['Score B']:.2f}")
    print("-" * 30)
    print(f"Critical Saves (A failed, B succeeded): {len(saves)}")
    saves = df[(df['Score A'] < 0.50) & (df['Score C'] > 0.80)]
    print("-" * 30)
    print(f"Critical Saves (A failed, C succeeded): {len(saves)}")
    print("-" * 30)
    if not saves.empty:
        print("Examples of fixed errors:")
        for i, row in saves.head(5).iterrows():
            print(f" - ID: {row['id']} ({row['type']}) | A: {row['Score A']:.2f} -> C: {row['Score C']:.2f}")

    # --- VISUALIZATION 1: Grouped Bar Chart by Category ---
    print("\nGenerating Category Comparison Chart...")
    plt.figure(figsize=(10, 6))
    
    # Melt dataframe for Seaborn
    df_melted = df.melt(id_vars=['id', 'type'], value_vars=['Score A', 'Score B', 'Score C'], 
                        var_name='Method', value_name='Score')
    
    # Create Bar Chart
    chart = sns.barplot(data=df_melted, x='type', y='Score', hue='Method', errorbar=None, palette="viridis")
    chart.set_title('Performance by Question Category', fontsize=16)
    chart.set_ylim(0, 1.1)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('comparison_chart.png')
    print(" -> Saved to comparison_chart.png")

    # --- VISUALIZATION 2: Radar Chart (The "Skill Shape") ---
    # This shows strengths/weaknesses
    print("Generating Radar Chart...")
    
    # Aggregate scores by category
    cat_scores = df.groupby('type')[['Score A', 'Score B', 'Score C']].mean()
    
    # Setup for radar chart
    labels = cat_scores.index.tolist()
    num_vars = len(labels)
    
    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] # Close the loop

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Draw Method A
    values_a = cat_scores['Score A'].tolist()
    values_a += values_a[:1] # Close the loop
    ax.plot(angles, values_a, color='red', linewidth=2, label='Method A (Image Only)')
    ax.fill(angles, values_a, color='red', alpha=0.25)
    
    # Draw Method B
    values_b = cat_scores['Score B'].tolist()
    values_b += values_b[:1] # Close the loop
    ax.plot(angles, values_b, color='blue', linewidth=2, label='Method B (Image + JSON)')
    ax.fill(angles, values_b, color='blue', alpha=0.25)
    
    # Draw Method B
    values_c = cat_scores['Score C'].tolist()
    values_c += values_c[:1] # Close the loop
    ax.plot(angles, values_c, color='green', linewidth=2, label='Method C (JSON Only)')
    ax.fill(angles, values_c, color='green', alpha=0.25)
    
    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=12)
    ax.set_title("Capability Radar: Vision vs. Grounded Vision", size=15, y=1.1)
    ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    plt.savefig('radar_chart.png')
    print(" -> Saved to radar_chart.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default='extraction_results.json', help='Path to results JSON')
    args = parser.parse_args()
    
    analyze(args.file)
