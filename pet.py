import tkinter as tk
from PIL import Image, ImageTk
import os
import math
import time

# -------------------------
# Helper: load sprites (absolute path)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_sprites(folder):
    frames = []
    path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(path):
        print(f"[Missing folder] {path}")
        return frames
    for f in sorted(os.listdir(path)):
        if f.lower().endswith(".png"):
            try:
                img = Image.open(os.path.join(path, f)).convert("RGBA")
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(img))
            except Exception as e:
                print(f"Error loading {f}: {e}")
    print(f"Loaded {len(frames)} sprites from {folder}")
    return frames


# -------------------------
# Desktop Pet
# -------------------------
class DesktopPet:
    def __init__(self, start_x=300, start_y=200):
        # window
        self.root = tk.Toplevel()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        # transparent background setup for Windows
        transparent = "magenta"
        self.root.config(bg=transparent)
        self.root.wm_attributes("-transparentcolor", transparent)

        # canvas for sprite
        self.canvas = tk.Canvas(self.root, width=100, height=100,
                                bg=transparent, highlightthickness=0)
        self.canvas.pack()

        # load animations (folders expected under project/sprites/)
        self.s_idle = load_sprites("sprites/idle")
        self.s_walk = load_sprites("sprites/walk")
        self.s_headpat = load_sprites("sprites/headpat")
        self.s_surf = load_sprites("sprites/surf")
        self.s_hover = load_sprites("sprites/hover")

        if not self.s_idle:
            raise ValueError("No idle sprites found. Add sprites/idle with PNGs.")

        # fallbacks so missing sets don't crash
        if not self.s_walk:
            self.s_walk = self.s_idle
        if not self.s_headpat:
            self.s_headpat = self.s_idle
        if not self.s_surf:
            self.s_surf = self.s_idle
        if not self.s_hover:
            self.s_hover = self.s_idle

        # sprite geometry & state
        self.sprite_w = 80
        self.sprite_h = 80
        self.current = 0
        self.state = "idle"
        self.interaction_radius = 120  # only react within this many pixels

        # place window
        self.pet_x = start_x
        self.pet_y = start_y
        self.root.geometry(f"+{self.pet_x}+{self.pet_y}")

        # create image item and bind events to the item (so hover is exact)
        self.pet_item = self.canvas.create_image(50, 50, image=self.s_idle[0])
        self.canvas.tag_bind(self.pet_item, "<Enter>", self.on_hover_enter)
        self.canvas.tag_bind(self.pet_item, "<Leave>", self.on_hover_exit)
        self.canvas.tag_bind(self.pet_item, "<Button-3>", self.show_menu)

        self.hovering = False
        self.last_update = time.time()

        self.animate()

    # right-click menu (on the sprite)
    def show_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Close Pet", command=self.close)
        menu.tk_popup(event.x_root, event.y_root)

    def close(self):
        try:
            self.root.destroy()
        except:
            pass

    # hover callbacks (exactly when mouse is over the sprite image)
    def on_hover_enter(self, event):
        self.hovering = True

    def on_hover_exit(self, event):
        self.hovering = False

    # compute state using interaction radius & directional logic
    def update_state_based_on_mouse(self):
        mx = self.root.winfo_pointerx()
        my = self.root.winfo_pointery()

        # current window position
        self.pet_x = self.root.winfo_x()
        self.pet_y = self.root.winfo_y()

        center_x = self.pet_x + (self.canvas.winfo_width() // 2)
        center_y = self.pet_y + (self.canvas.winfo_height() // 2)

        dx = mx - center_x
        dy = my - center_y
        distance = math.hypot(dx, dy)

        # outside interaction radius -> idle
        if distance > self.interaction_radius:
            # keep hover until mouse leaves the item (so hover isn't immediately lost)
            if not self.hovering:
                self.state = "idle"
            return

        # hover has priority (mouse on the pet item)
        if self.hovering:
            self.state = "hover"
            return

        # now decide directional states when mouse is close
        # prioritize vertical headpat/surf if vertically dominant
        if abs(dx) < 40 and dy < -30:
            self.state = "headpat"
            return
        if dy > 50:
            self.state = "surf"
            return

        # horizontal dominance -> walk left/right
        if abs(dx) > abs(dy):
            if dx > 0:
                self.state = "right"
            else:
                self.state = "left"
        else:
            # fallback to idle if we can't pick a direction
            self.state = "idle"

    # main animation loop
    def animate(self):
        now = time.time()
        # throttle small updates to avoid super-fast geometry changes
        if now - self.last_update >= 0.05:
            self.update_state_based_on_mouse()
            self.last_update = now

        # movement when walking
        if self.state == "right":
            # move window a little right
            self.pet_x += 2
            self.root.geometry(f"+{self.pet_x}+{self.pet_y}")
            sprites = self.s_walk
        elif self.state == "left":
            self.pet_x -= 2
            self.root.geometry(f"+{self.pet_x}+{self.pet_y}")
            sprites = self.s_walk
        elif self.state == "headpat":
            sprites = self.s_headpat
        elif self.state == "surf":
            sprites = self.s_surf
        elif self.state == "hover":
            sprites = self.s_hover
        else:
            sprites = self.s_idle

        # safe guard in case a sprite list is empty
        if not sprites:
            sprites = self.s_idle

        frame = sprites[self.current % len(sprites)]
        self.canvas.itemconfig(self.pet_item, image=frame)
        self.current += 1

        # schedule next frame
        self.root.after(120, self.animate)


# -------------------------
# Launcher GUI
# -------------------------
class Launcher:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Desktop Pet")
        self.win.geometry("280x140")
        self.win.resizable(False, False)

        tk.Label(self.win, text="Your Desktop Pet", font=("Segoe UI", 12)).pack(pady=(12, 6))

        self.activate_btn = tk.Button(self.win, text="Activate", font=("Arial", 12), command=self.launch_pet)
        self.activate_btn.pack(pady=10)

        tk.Label(self.win, text="Right-click pet → Close", font=("Segoe UI", 8)).pack(pady=(4, 0))

        self.win.mainloop()

    def launch_pet(self):
        # spawn the pet and disable activate to avoid duplicates
        DesktopPet(start_x=400, start_y=200)
        self.activate_btn.config(state="disabled")


if __name__ == "__main__":
    Launcher()
