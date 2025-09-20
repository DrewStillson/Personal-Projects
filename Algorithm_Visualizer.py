"""
Algorithm Visualizer using Pygame
---------------------------------
Author: Drew Stillson
Date: 8/05/2025

This program visualizes common sorting algorithms in real-time using Pygame.
The goal is to help students and learners see how different algorithms operate
step-by-step on a list of values. Each sorting algorithm is implemented as a
generator that yields after each "step" so the visualization can update.

Algorithms included:
- Bubble Sort
- Selection Sort
- Insertion Sort
- Merge Sort
- Quick Sort
- Heap Sort

Controls:
- SPACE : Start the currently selected sort
- R     : Reset the list with new random values
- A     : Set sort order to ascending
- D     : Set sort order to descending
- B     : Select Bubble Sort
- S     : Select Selection Sort
- I     : Select Insertion Sort
- M     : Select Merge Sort
- Q     : Select Quick Sort
- H     : Select Heap Sort
"""

import pygame
import random

pygame.init()


class SetUpInfo:
    """Container for configuration constants and Pygame window setup."""

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    GREY = (128, 128, 128)

    # Display settings
    BACKGROUND_COLOR = WHITE
    EXTRA_SPACE_SIDE = 200
    EXTRA_SPACE_TOP = 150
    FPS = 60
    HEIGHT = 800
    WIDTH = 800

    # List settings
    LIST_LENGTH = 50
    MIN_NUM = 0
    MAX_NUM = 100

    # Fonts
    FONT = pygame.font.SysFont('bahnschrift', 15)
    TITLE_FONT = pygame.font.SysFont('bahnschrift', 30)

    def __init__(self):
        """Initialize the window and generate an initial list of values."""
        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Algorithm Visualizer")
        self.values = self.generate_list()
        self.col_dimensions()

    def col_dimensions(self):
        """Calculate bar dimensions based on window and list size."""
        self.col_width = round(
            (self.WIDTH - self.EXTRA_SPACE_SIDE) / self.LIST_LENGTH
        )
        self.col_height = round(
            (self.HEIGHT - self.EXTRA_SPACE_TOP) /
            (self.MAX_NUM - self.MIN_NUM)
        )
        self.start_x = self.EXTRA_SPACE_SIDE // 2

    def generate_list(self):
        """Return a new randomized list of integers."""
        return [
            random.randint(self.MIN_NUM, self.MAX_NUM)
            for _ in range(self.LIST_LENGTH)
        ]


def draw_window(info, name, ascending):
    """
    Clear the window and draw the header information plus the current list.

    Args:
        info (SetUpInfo): Configuration and window context.
        name (str): Current algorithm name and complexity string.
        ascending (bool): True for ascending order, False for descending.
    """
    info.window.fill(info.BACKGROUND_COLOR)

    # Title and controls text
    sort_title = info.TITLE_FONT.render(
        f"{name} - {'ASCENDING' if ascending else 'DESCENDING'}",
        True,
        info.GREEN,
    )
    controls = info.FONT.render(
        "SPACE - START | R - RESET | A - ASCENDING | D - DESCENDING",
        True,
        info.BLACK,
    )
    sort_controls = info.FONT.render(
        "B - BUBBLE | S - SELECTION | I - INSERTION | M - MERGE | Q - QUICK | H - HEAP",
        True,
        info.BLACK,
    )

    # Blit to window
    info.window.blit(sort_title,
                     (info.WIDTH / 2 - sort_title.get_width() / 2, 5))
    info.window.blit(controls,
                     (info.WIDTH / 2 - controls.get_width() / 2, 45))
    info.window.blit(sort_controls,
                     (info.WIDTH / 2 - sort_controls.get_width() / 2, 65))

    draw_list(info)
    pygame.display.update()


def draw_list(info, color_col={}, clear=False):
    """
    Draw the list of values as vertical bars.

    Args:
        info (SetUpInfo): Window context and values.
        color_col (dict): Mapping of index -> color for highlighting.
        clear (bool): If True, clear the drawing area before drawing.
    """
    values = info.values

    if clear:
        clear_rect = (
            info.EXTRA_SPACE_SIDE // 2,
            info.EXTRA_SPACE_TOP,
            info.WIDTH - info.EXTRA_SPACE_SIDE,
            info.HEIGHT - info.EXTRA_SPACE_TOP,
        )
        pygame.draw.rect(info.window, info.BACKGROUND_COLOR, clear_rect)

    for i, value in enumerate(values):
        x = info.start_x + i * info.col_width
        y = info.HEIGHT - (value - info.MIN_NUM) * info.col_height

        # Generate shade based on value
        normalize = (value - info.MIN_NUM) / (info.MAX_NUM - info.MIN_NUM)
        shade = int(255 - 155 * normalize)
        color = (shade, shade, shade)

        if i in color_col:
            color = color_col[i]

        pygame.draw.rect(info.window, color,
                         (x, y, info.col_width, info.HEIGHT))
        pygame.draw.rect(info.window, info.BLACK,
                         (x, y, info.col_width, info.HEIGHT), 1)

    if clear:
        pygame.display.update()


# -------------------
# Sorting Algorithms
# -------------------

def bubble_sort(info, ascending=True):
    """Bubble Sort: repeatedly swap adjacent out-of-order pairs."""
    values = info.values
    for i in range(len(values) - 1):
        for j in range(len(values) - 1 - i):
            num1, num2 = values[j], values[j + 1]
            if (num1 > num2 and ascending) or (num1 < num2 and not ascending):
                values[j], values[j + 1] = values[j + 1], values[j]
                draw_list(info, {j: info.GREEN, j + 1: info.RED}, True)
                yield True
    return values


def selection_sort(info, ascending=True):
    """Selection Sort: repeatedly select the min/max and put in place."""
    values = info.values
    for i in range(len(values)):
        min_index = i
        for j in range(i + 1, len(values)):
            if (values[j] < values[min_index] and ascending) or \
               (values[j] > values[min_index] and not ascending):
                min_index = j
            draw_list(info, {i: info.GREEN, j: info.RED}, True)
            yield True

        values[i], values[min_index] = values[min_index], values[i]
        draw_list(info, {i: info.GREEN, min_index: info.RED}, True)
        yield True
    return values


def insertion_sort(info, ascending=True):
    """Insertion Sort: insert each element into its correct sorted spot."""
    values = info.values
    for i in range(1, len(values)):
        key = values[i]
        j = i - 1

        while j >= 0 and (
            (key < values[j] and ascending) or
            (key > values[j] and not ascending)
        ):
            values[j + 1] = values[j]
            draw_list(info, {j: info.RED, j + 1: info.GREEN}, True)
            yield True
            j -= 1

        values[j + 1] = key
        draw_list(info, {j: info.RED, j + 1: info.GREEN}, True)
        yield True
    return values


# Merge Sort and helpers
def merge_sort(info, ascending=True):
    """Merge Sort: divide and conquer sort with O(n log n) complexity."""
    values = info.values
    if len(values) <= 1:
        return values
    yield from _merge_sort(values, 0, len(values) - 1, info, ascending)
    return values


def _merge_sort(a, l, r, info, ascending):
    if l >= r:
        return
    m = (l + r) // 2
    yield from _merge_sort(a, l, m, info, ascending)
    yield from _merge_sort(a, m + 1, r, info, ascending)
    yield from _merge(a, l, m, r, info, ascending)


def _merge(a, l, m, r, info, ascending):
    left = a[l:m + 1]
    right = a[m + 1:r + 1]
    i = j = 0
    k = l

    while i < len(left) and j < len(right):
        li = l + i
        rj = m + 1 + j
        cmp = left[i] <= right[j] if ascending else left[i] >= right[j]
        draw_list(info, {li: info.GREEN, rj: info.GREEN, k: info.RED}, True)
        yield True

        if cmp:
            a[k] = left[i]
            i += 1
        else:
            a[k] = right[j]
            j += 1

        draw_list(info, {k: info.RED}, True)
        yield True
        k += 1

    while i < len(left):
        a[k] = left[i]
        draw_list(info, {k: info.RED}, True)
        yield True
        i += 1
        k += 1

    while j < len(right):
        a[k] = right[j]
        draw_list(info, {k: info.RED}, True)
        yield True
        j += 1
        k += 1


# Quick Sort and helpers
def quick_sort(info, ascending=True):
    """Quick Sort: partition-based divide and conquer."""
    values = info.values
    if len(values) <= 1:
        return values
    yield from _quick_sort(values, 0, len(values) - 1, info, ascending)
    return values


def _quick_sort(a, low, high, info, ascending):
    if low < high:
        p = yield from _partition(a, low, high, info, ascending)
        yield from _quick_sort(a, low, p - 1, info, ascending)
        yield from _quick_sort(a, p + 1, high, info, ascending)


def _partition(a, low, high, info, ascending):
    pivot = a[high]
    i = low - 1
    draw_list(info, {high: info.RED}, True)
    yield True

    for j in range(low, high):
        cmp = a[j] <= pivot if ascending else a[j] >= pivot
        draw_list(info, {j: info.GREEN, high: info.RED}, True)
        yield True

        if cmp:
            i += 1
            if i != j:
                a[i], a[j] = a[j], a[i]
                draw_list(info, {i: info.RED, j: info.GREEN, high: info.RED}, True)
                yield True

    if (i + 1) != high:
        a[i + 1], a[high] = a[high], a[i + 1]
        draw_list(info, {i + 1: info.RED, high: info.GREEN}, True)
        yield True
    return i + 1


# Heap Sort and helpers
def heap_sort(info, ascending=True):
    """Heap Sort: build a heap, then repeatedly extract the root."""
    a = info.values
    n = len(a)

    # Build heap
    for i in range(n // 2 - 1, -1, -1):
        yield from _heapify(a, n, i, info, make_max=ascending)

    # Extract elements
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        draw_list(info, {0: info.RED, end: info.GREEN}, True)
        yield True
        yield from _heapify(a, end, 0, info, make_max=ascending)
    return a


def _heapify(a, heap_size, i, info, make_max=True):
    """Helper to maintain heap property from index i downwards."""
    while True:
        l = 2 * i + 1
        r = 2 * i + 2
        best = i

        if l < heap_size:
            draw_list(info, {l: info.GREEN, best: info.RED}, True)
            yield True
            if (a[l] > a[best]) if make_max else (a[l] < a[best]):
                best = l

        if r < heap_size:
            draw_list(info, {r: info.GREEN, best: info.RED}, True)
            yield True
            if (a[r] > a[best]) if make_max else (a[r] < a[best]):
                best = r

        if best != i:
            a[i], a[best] = a[best], a[i]
            draw_list(info, {i: info.RED, best: info.GREEN}, True)
            yield True
            i = best
        else:
            break


# -------------------
# Main Loop
# -------------------

def main():
    run = True
    sorting = False
    ascending = True
    algorithm = bubble_sort
    name = "BUBBLE SORT O(n^2)"
    generator = None

    clock = pygame.time.Clock()
    info = SetUpInfo()

    while run:
        clock.tick(info.FPS)

        if sorting:
            try:
                next(generator)
            except StopIteration:
                sorting = False
        else:
            draw_window(info, name, ascending)

        pygame.display.update()

        # Handle input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    info.values = info.generate_list()
                    sorting = False
                elif event.key == pygame.K_SPACE and not sorting:
                    sorting = True
                    generator = algorithm(info, ascending)
                elif event.key == pygame.K_a and not sorting:
                    ascending = True
                elif event.key == pygame.K_d and not sorting:
                    ascending = False
                elif event.key == pygame.K_b and not sorting:
                    name = "BUBBLE SORT O(n^2)"
                    algorithm = bubble_sort
                elif event.key == pygame.K_i and not sorting:
                    name = "INSERTION SORT O(n^2)"
                    algorithm = insertion_sort
                elif event.key == pygame.K_s and not sorting:
                    name = "SELECTION SORT O(n^2)"
                    algorithm = selection_sort
                elif event.key == pygame.K_m and not sorting:
                    name = "MERGE SORT O(n log n)"
                    algorithm = merge_sort
                elif event.key == pygame.K_q and not sorting:
                    name = "QUICK SORT O(n log n)"
                    algorithm = quick_sort
                elif event.key == pygame.K_h and not sorting:
                    name = "HEAP SORT O(n log n)"
                    algorithm = heap_sort

    pygame.quit()


if __name__ == "__main__":
    main()
