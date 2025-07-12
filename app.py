import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CutOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Cutlist Optimizer")
        self.root.geometry("900x700")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', padding=6)
        self.style.configure('TLabel', background='#f0f0f0')
        
        self.create_widgets()
        self.cuts = []
        self.stock_lengths = [2400]  # Default stock length in mm
        self.results = []
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding="10")
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Stock length input
        ttk.Label(input_frame, text="Stock Length (mm):").grid(row=0, column=0, sticky=tk.W)
        self.stock_entry = ttk.Entry(input_frame, width=10)
        self.stock_entry.insert(0, "2400")
        self.stock_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Cut length input
        ttk.Label(input_frame, text="Cut Length (mm):").grid(row=1, column=0, sticky=tk.W)
        self.cut_length_entry = ttk.Entry(input_frame, width=10)
        self.cut_length_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Quantity input
        ttk.Label(input_frame, text="Quantity:").grid(row=1, column=2, sticky=tk.W, padx=10)
        self.quantity_entry = ttk.Entry(input_frame, width=8)
        self.quantity_entry.grid(row=1, column=3, sticky=tk.W)
        
        # Add cut button
        add_button = ttk.Button(input_frame, text="Add Cut", command=self.add_cut)
        add_button.grid(row=1, column=4, padx=10)
        
        # Clear button
        clear_button = ttk.Button(input_frame, text="Clear All", command=self.clear_cuts)
        clear_button.grid(row=0, column=4, padx=10)
        
        # Cuts list display
        self.cuts_tree = ttk.Treeview(main_frame, columns=("length", "quantity"), show="headings", height=10)
        self.cuts_tree.heading("length", text="Length (mm)")
        self.cuts_tree.heading("quantity", text="Quantity")
        self.cuts_tree.column("length", width=150)
        self.cuts_tree.column("quantity", width=100)
        self.cuts_tree.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Remove selected button
        remove_button = ttk.Button(main_frame, text="Remove Selected", command=self.remove_selected)
        remove_button.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Optimization controls
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        optimize_button = ttk.Button(control_frame, text="Optimize Cuts", command=self.optimize)
        optimize_button.pack(side=tk.LEFT, padx=5)
        
        visualize_button = ttk.Button(control_frame, text="Visualize", command=self.visualize)
        visualize_button.pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Optimization Results", padding="10")
        results_frame.grid(row=4, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.results_text = tk.Text(results_frame, height=10, width=80)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Visualization area
        self.visualization_frame = ttk.Frame(main_frame)
        self.visualization_frame.grid(row=5, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
    
    def add_cut(self):
        try:
            length = float(self.cut_length_entry.get())
            quantity = int(self.quantity_entry.get())
            
            if length <= 0 or quantity <= 0:
                raise ValueError("Values must be positive")
            
            self.cuts.append((length, quantity))
            self.update_cuts_list()
            
            # Clear the input fields
            self.cut_length_entry.delete(0, tk.END)
            self.quantity_entry.delete(0, tk.END)
            self.cut_length_entry.focus()
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numbers:\n{e}")
    
    def remove_selected(self):
        selected = self.cuts_tree.selection()
        if selected:
            item = self.cuts_tree.item(selected)
            length, quantity = item['values']
            self.cuts.remove((length, quantity))
            self.update_cuts_list()
    
    def clear_cuts(self):
        self.cuts = []
        self.update_cuts_list()
    
    def update_cuts_list(self):
        # Clear the tree
        for row in self.cuts_tree.get_children():
            self.cuts_tree.delete(row)
        
        # Add new items
        for length, quantity in self.cuts:
            self.cuts_tree.insert("", tk.END, values=(length, quantity))
    
    def optimize(self):
        try:
            stock_length = float(self.stock_entry.get())
            if not self.cuts:
                raise ValueError("Please add at least one cut")
            
            # First-Fit Decreasing algorithm for bin packing
            self.results = []
            cuts_to_allocate = sorted([(l, q) for l, q in self.cuts], key=lambda x: -x[0])
            cuts_expanded = []
            
            # Expand all cuts into individual pieces
            for length, quantity in cuts_to_allocate:
                cuts_expanded.extend([length] * quantity)
            
            # Bin packing algorithm
            bins = []
            bin_capacity = stock_length
            
            for cut in sorted(cuts_expanded, reverse=True):
                placed = False
                for bin in bins:
                    if sum(bin) + cut <= bin_capacity:
                        bin.append(cut)
                        placed = True
                        break
                
                if not placed:
                    bins.append([cut])
            
            # Save results
            self.results = bins
            
            # Display results
            self.results_text.delete(1.0, tk.END)
            total_stock = len(bins)
            total_waste = sum([bin_capacity - sum(bin) for bin in bins])
            efficiency = (1 - (total_waste / (total_stock * bin_capacity))) * 100
            
            self.results_text.insert(tk.END, f"Optimization Results:\n")
            self.results_text.insert(tk.END, f"- Total stock pieces needed: {total_stock}\n")
            self.results_text.insert(tk.END, f"- Total waste: {total_waste:.2f} mm\n")
            self.results_text.insert(tk.END, f"- Efficiency: {efficiency:.2f}%\n\n")
            
            for i, bin in enumerate(bins, 1):
                waste = bin_capacity - sum(bin)
                self.results_text.insert(tk.END, f"Stock Piece {i}:\n")
                self.results_text.insert(tk.END, f"- Cuts: {', '.join(map(str, bin))}\n")
                self.results_text.insert(tk.END, f"- Waste: {waste:.2f} mm ({waste/bin_capacity:.1%})\n\n")
        
        except ValueError as e:
            messagebox.showerror("Optimization Error", str(e))
    
    def visualize(self):
        if not self.results:
            messagebox.showwarning("Visualization", "Please run optimization first")
            return
        
        # Clear previous visualization
        for widget in self.visualization_frame.winfo_children():
            widget.destroy()
        
        stock_length = float(self.stock_entry.get())
        
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.set_facecolor('#f0f0f0')
        
        # Colors for different cut lengths
        colors = plt.cm.tab20c.colors
        
        for i, bin in enumerate(self.results):
            current_pos = 0
            for j, cut in enumerate(bin):
                color_idx = j % len(colors)
                ax.barh(i, cut, left=current_pos, color=colors[color_idx], edgecolor='black')
                # Add text label
                ax.text(current_pos + cut/2, i, f"{cut}mm", ha='center', va='center', color='white')
                current_pos += cut
            
            # Add waste portion
            waste = stock_length - sum(bin)
            ax.barh(i, waste, left=current_pos, color='lightgray', edgecolor='black', alpha=0.7)
        
        ax.set_yticks(range(len(self.results)))
        ax.set_yticklabels([f"Stock {i+1}" for i in range(len(self.results))])
        ax.set_xlabel('Length (mm)')
        ax.set_title('Cut Optimization Visualization')
        ax.grid(True, axis='x', alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=self.visualization_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = CutOptimizerApp(root)
    root.mainloop()





























