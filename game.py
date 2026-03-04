import numpy as np
import matplotlib.pyplot as plt

# --- Game state ---
points = []
point_colors = []
colors = ['blue', 'red', 'green', 'yellow']
player_names = {c: f"Player {c.capitalize()}" for c in colors}
budgets = {c: 100.0 for c in colors}
count = np.zeros(len(colors), dtype=int)
turn = 0
player_status = {c: 1 for c in colors}

# --- Rendering ---
grid_size = 500
fig = plt.figure(figsize=(10, 6))
ax = fig.add_axes([0.06, 0.08, 0.66, 0.84])       # main board
ax_table = fig.add_axes([0.76, 0.08, 0.20, 0.84]) # scoreboard
ax_table.axis('off')

nearest_point_color = None
distance = None

# Pastel fill colors for territories & table swatches
color_map = {
    'blue':   (0.68, 0.85, 0.90, 1),  # light steel/cyan
    'red':    (0.94, 0.50, 0.50, 1),
    'green':  (0.50, 0.85, 0.50, 1),
    'yellow': (0.95, 0.85, 0.30, 1),
}

def compute_voronoi():
    global nearest_point_color, distance
    x = np.linspace(0, 1, grid_size)
    y = np.linspace(0, 1, grid_size)
    X, Y = np.meshgrid(x, y)

    if not points:
        nearest_point_color = np.full(X.shape, None, dtype=object)
        distance = np.full(X.shape, np.inf)
        return

    distance = np.full(X.shape, np.inf)
    nearest_point_color = np.empty(X.shape, dtype=object)

    # Manhattan metric; use np.hypot for Euclidean
    for i, (px, py) in enumerate(points):
        D = np.abs(X - px) + np.abs(Y - py)
        mask = D < distance
        distance[mask] = D[mask]
        nearest_point_color[mask] = point_colors[i]

def calc_area_shares():
    total_area = grid_size * grid_size
    shares = {c: 0.0 for c in colors}
    if nearest_point_color is None:
        return shares
    for c in colors:
        shares[c] = float(np.sum(nearest_point_color == c)) / total_area
    return shares

def draw_scoreboard(area_shares, incomes, costs):
    """Draw/update the table on the right, with readable color swatches and turn highlight."""
    ax_table.clear()
    ax_table.axis('off')

    headers = ["Player", "Pts", "Share", "Inc", "Cost", "Budget", "Status"]
    data = []
    for i, c in enumerate(colors):
        status = "Alive" if player_status[c] == 1 else "Lost"
        row = [
            player_names[c],
            int(count[i]),
            f"{area_shares[c]*100:0.1f}%",
            f"{incomes[c]:0.1f}",
            f"{costs[c]:0.1f}",
            f"{budgets[c]:0.1f}",
            status,
        ]
        data.append(row)

    table = ax_table.table(
        cellText=data,
        colLabels=headers,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.2)

    # Make the Player column cells a pastel swatch of the player's color, keep text black for readability
    player_col_index = 0
    for i, c in enumerate(colors):
        cell = table[(i + 1, player_col_index)]  # +1 for header row
        cell.set_facecolor(color_map[c])
        cell.get_text().set_color('black')
        cell.get_text().set_weight('bold')

    # Highlight current player's row (outline only so it doesn't clash with the color swatch)
    current_color = colors[turn]
    current_row = colors.index(current_color)
    for col in range(len(headers)):
        body_cell = table[(current_row + 1, col)]
        body_cell.set_edgecolor('black')
        body_cell.set_linewidth(2.5)

    ax_table.set_title(
        f"Scoreboard — Turn: {player_names[current_color]}",
        fontsize=11, fontweight='bold', pad=8
    )

def plot_voronoi(area_shares, incomes, costs, event=None):
    ax.clear()
    compute_voronoi()

    # Paint territories
    image = np.zeros((grid_size, grid_size, 4))
    for c, rgba in color_map.items():
        if nearest_point_color is not None:
            mask = (nearest_point_color == c)
            image[mask] = rgba
    ax.imshow(image, origin='lower', extent=(0, 1, 0, 1))

    # Points (constant styling — no turn-based changes)
    for (px, py), c in zip(points, point_colors):
        ax.plot(px, py, 'o', color=c, markeredgecolor='black', markeredgewidth=1.0, ms=6, zorder=5)

    # Border & grid
    ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color='black', linewidth=2)
    ax.set_xticks(np.linspace(0, 1, 11))
    ax.set_yticks(np.linspace(0, 1, 11))
    ax.grid(True)

    # Titles & backgrounds
    current_color = colors[turn]
    fig.suptitle(
        f"Location, Location, Location!  —  Turn: {player_names[current_color]}",
        fontsize=16, fontweight='bold', x=0.45
    )
    fig.patch.set_facecolor('#fff1e5')
    ax.set_facecolor('#fff1e5')

    # Draw the scoreboard on the right
    draw_scoreboard(area_shares, incomes, costs)

    plt.pause(0.001)

def on_click(event):
    global turn
    if event.inaxes is None or event.inaxes not in (ax,):
        return

    x, y = float(event.xdata), float(event.ydata)
    current_idx = turn
    current_color = colors[current_idx]

    movetype = 0  # 1 add, 2 remove

    # If budget >= 0 and alive -> place; else must remove own point at click
    if budgets[current_color] >= 0 and player_status[current_color] == 1:
        points.append([x, y])
        point_colors.append(current_color)
        count[current_idx] += 1
        movetype = 1
    else:
        removed = False
        for i, ((px, py), c) in enumerate(list(zip(points, point_colors))):
            if c == current_color and np.isclose(px, x, atol=0.01) and np.isclose(py, y, atol=0.01):
                points.pop(i); point_colors.pop(i)
                count[current_idx] -= 1
                removed = True
                movetype = 2
                break
        if not removed:
            print(f"{player_names[current_color]} must remove one of their own points!")
            return

    # Recompute shares/incomes
    compute_voronoi()
    area_shares = calc_area_shares()
    incomes = {c: area_shares[c] * 100 for c in colors}

    # Base cost 5 per point you own
    costs = {c: 10 * count[i] for i, c in enumerate(colors)}

    # Placement/removal adjustment (±5)
    if movetype == 1:
        costs[current_color] += 20
    elif movetype == 2:
        costs[current_color] = costs[current_color] - 10

    # Update budgets
    for c in colors:
        budgets[c] += incomes[c]
        budgets[c] -= costs[c]

    # Lose condition
    if budgets[current_color] < 0 and count[current_idx] == 0:
        player_status[current_color] = 0

    # Advance to next alive player
    for _ in range(len(colors)):
        turn = (turn + 1) % len(colors)
        if player_status[colors[turn]] == 1:
            break

    plot_voronoi(area_shares, incomes, costs)

# --- Initial draw ---
compute_voronoi()
area_shares = calc_area_shares()
incomes = {c: area_shares[c] * 100 for c in colors}
costs = {c: 0.0 for c in colors}
plot_voronoi(area_shares, incomes, costs)

# Connect the click handler ONCE
cid = fig.canvas.mpl_connect('button_press_event', on_click)
plt.show()
