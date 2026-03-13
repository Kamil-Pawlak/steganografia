import customtkinter as ctk
from tkinter import filedialog
from stego_logic.bmp_handler import calculate_capacity, format_size
import os
import zlib
from stego_logic.encoder import encode_data
from stego_logic.decoder import check_if_encoded, decode_data
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Steganography App")
        self.geometry("900x700") # Lekko poszerzyłem okno, żeby miniatury ładnie się zmieściły

        # --- LEWA KOLUMNA ---
        self.left_frame = ctk.CTkFrame(self, width=250)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        # Przycisk wyboru nośnika
        self.select_carrier_button = ctk.CTkButton(self.left_frame, text="Wybierz nośnik (BMP)", command=self.select_carrier)
        self.select_carrier_button.pack(pady=10, padx=20, fill="x")
        self.carrier_path_label = ctk.CTkLabel(self.left_frame, text="Brak wybranego pliku", font=("Arial", 10))
        self.carrier_path_label.pack(pady=(0, 10))
        
        # Przycisk wyboru pliku do ukrycia
        self.select_file_button = ctk.CTkButton(self.left_frame, text="Wybierz plik do ukrycia", command=self.select_file)
        self.select_file_button.pack(pady=10, padx=20, fill="x")
        self.file_path_label = ctk.CTkLabel(self.left_frame, text="Brak wybranego pliku", font=("Arial", 10))
        self.file_path_label.pack(pady=(0, 10))
        
        # Sekcja parametrów (suwaki dla RGB)
        self.params_frame = ctk.CTkFrame(self.left_frame)
        self.params_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.params_frame, text="Liczba bitów - RED:").pack()
        self.red_slider = ctk.CTkSlider(self.params_frame, from_=0, to=8, number_of_steps=8)
        self.red_slider.pack(pady=(0, 10))
        
        ctk.CTkLabel(self.params_frame, text="Liczba bitów - GREEN:").pack()
        self.green_slider = ctk.CTkSlider(self.params_frame, from_=0, to=8, number_of_steps=8)
        self.green_slider.pack(pady=(0, 10))
        
        ctk.CTkLabel(self.params_frame, text="Liczba bitów - BLUE:").pack()
        self.blue_slider = ctk.CTkSlider(self.params_frame, from_=0, to=8, number_of_steps=8)
        self.blue_slider.pack(pady=(0, 10))
        
        # Ustawienie domyślnych wartości na 1
        self.red_slider.set(1)
        self.green_slider.set(1)
        self.blue_slider.set(1)

        # Sekcja akcji
        self.capacity_button = ctk.CTkButton(self.left_frame, text="Test pojemności nośnika", command=self.test_capacity)
        self.capacity_button.pack(pady=10, padx=20, fill="x")
        
        self.check_hidden_button = ctk.CTkButton(self.left_frame, text="Sprawdź czy plik zawiera ukryte dane", command=self.check_hidden)
        self.check_hidden_button.pack(pady=10, padx=20, fill="x")
        
        self.hide_button = ctk.CTkButton(self.left_frame, text="Ukryj dane", command=self.hide_data, fg_color="green")
        self.hide_button.pack(pady=10, padx=20, fill="x")
        
        self.reveal_button = ctk.CTkButton(self.left_frame, text="Odkryj dane", command=self.reveal_data)
        self.reveal_button.pack(pady=10, padx=20, fill="x")
        

        # prawa kolumna - podgląd i statystyki
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.right_frame, text="Podgląd i Statystyki", font=("Arial", 18, "bold")).pack(pady=10)

        # Ramka na miniatury 
        self.images_frame = ctk.CTkFrame(self.right_frame)
        self.images_frame.pack(pady=10, padx=10, fill="x")

        self.img_before_label = ctk.CTkLabel(self.images_frame, text="Obraz PRZED\n(Brak pliku)", width=250, height=200, fg_color="gray20")
        self.img_before_label.pack(side="left", expand=True, padx=10, pady=10)

        self.img_after_label = ctk.CTkLabel(self.images_frame, text="Obraz PO\n(Brak pliku)", width=250, height=200, fg_color="gray20")
        self.img_after_label.pack(side="right", expand=True, padx=10, pady=10)

        # Ramka na statystyki 
        self.stats_frame = ctk.CTkFrame(self.right_frame)
        self.stats_frame.pack(pady=10, padx=10, fill="x")

        self.stat_capacity = ctk.CTkLabel(self.stats_frame, text="Pojemność nośnika: ---", font=("Arial", 14))
        self.stat_capacity.pack(anchor="w", padx=20, pady=5)
        
        self.stat_file_size = ctk.CTkLabel(self.stats_frame, text="Rozmiar ukrywanego pliku: ---", font=("Arial", 14))
        self.stat_file_size.pack(anchor="w", padx=20, pady=5)

        self.stat_used = ctk.CTkLabel(self.stats_frame, text="Zajęte miejsce: ---", font=("Arial", 14))
        self.stat_used.pack(anchor="w", padx=20, pady=5)

        self.stat_free = ctk.CTkLabel(self.stats_frame, text="Wolne miejsce: ---", font=("Arial", 14))
        self.stat_free.pack(anchor="w", padx=20, pady=5)

        # Miejsce na wykres tortowy 
        self.chart_frame = ctk.CTkFrame(self.right_frame)
        self.chart_frame.pack(pady=10, padx=10, fill="both", expand=True)
        ctk.CTkLabel(self.chart_frame, text="Wykres zajętości").pack(expand=True)


    # --- METODY ---
    def select_carrier(self):
        filename = filedialog.askopenfilename(title="Wybierz plik BMP", filetypes=[("BMP Files", "*.bmp")])
        if filename:
            self.carrier_path = filename
            self.carrier_path_label.configure(text=filename.split("/")[-1])
            print(f"Wybrano nośnik: {filename}")
            # dodanie podglądu miniatury
            try:
                from PIL import Image, ImageTk
                img = Image.open(filename)
                img.thumbnail((250, 200))
                img_tk = ImageTk.PhotoImage(img)
                self.img_before_label.configure(image=img_tk, text="")
                self.img_before_label.image = img_tk  # zapobiega garbage collection
            except Exception as e:
                print(f"Nie można załadować miniatury: {e}")
                self.img_before_label.configure(text="Nie można załadować miniatury", image="")
                self.img_before_label.image = None

    def select_file(self):
        filename = filedialog.askopenfilename(title="Wybierz plik do ukrycia", filetypes=[("All Files", "*.*")])
        if filename:
            self.file_path = filename
            self.file_path_label.configure(text=filename.split("/")[-1])
            print(f"Wybrano plik do ukrycia: {filename}")

    def test_capacity(self):
        r_bits = int(self.red_slider.get())
        g_bits = int(self.green_slider.get())
        b_bits = int(self.blue_slider.get())
        
        self.carrier_path = getattr(self, 'carrier_path', None)
        secret_path = getattr(self, 'file_path', None)
        
        if not self.carrier_path:
            self.stat_capacity.configure(text="Pojemność nośnika: Brak wybranego pliku")
            return
        capacity_bytes = calculate_capacity(self.carrier_path, r_bits, g_bits, b_bits)
        self.stat_capacity.configure(text=f"Pojemność nośnika: {format_size(capacity_bytes)}")
        
        HEADER_SIZE = 64
        
        if secret_path and os.path.exists(secret_path):
            try:
                with open(secret_path, 'rb') as f:
                    secret_data = f.read()
                    
                compressed_data = zlib.compress(secret_data)
                compressed_size = len(compressed_data)
                
                total_size = HEADER_SIZE + compressed_size
                if total_size > capacity_bytes:
                    self.stat_file_size.configure(text=f"Rozmiar ukrywanego pliku: {format_size(len(secret_data))} (po kompresji: {format_size(compressed_size)}) - ZA DUŻY!")
                else:
                    self.stat_file_size.configure(text=f"Rozmiar ukrywanego pliku: {format_size(len(secret_data))} (po kompresji: {format_size(compressed_size)}) - OK")
            except Exception as e:
                self.stat_file_size.configure(text=f"Rozmiar ukrywanego pliku: Nie można odczytać pliku ({e})")
        else:
            self.stat_file_size.configure(text="Rozmiar ukrywanego pliku: Brak wybranego pliku")
        
        
        

    def check_hidden(self):
        print("Sprawdzanie ukrytych danych...")
        self.carrier_path = getattr(self, 'carrier_path', None)
        
        if not self.carrier_path:
            return
            
        try:
            if check_if_encoded(self.carrier_path):
                self.stat_used.configure(text="Status nośnika: ZAWIERA UKRYTE DANE", text_color="#ff4d4d") # Czerwony
            else:
                self.stat_used.configure(text="Status nośnika: PLIK JEST CZYSTY", text_color="#4dff4d") # Zielony
                
                
        except Exception as e:
            print(f"Błąd podczas sprawdzania: {e}")

    def hide_data(self):
        print("Ukrywanie danych...")
        self.carrier_path = getattr(self, 'carrier_path', None)
        secret_path = getattr(self, 'file_path', None)
        if not self.carrier_path or not secret_path:
            print("Brak nośnika lub pliku do ukrycia!")
            return
        r_bits = int(self.red_slider.get())
        g_bits = int(self.green_slider.get())
        b_bits = int(self.blue_slider.get())
        try:
            with open(secret_path, 'rb') as f:
                secret_data = f.read()
            compressed_size = len(zlib.compress(secret_data))
            total_used_bytes = 64 + compressed_size
            
            new_image = encode_data(self.carrier_path, secret_path, r_bits, g_bits, b_bits)
            #wyświetlamy miniaturę nowego obrazu
            display_image = new_image.copy()
            display_image.thumbnail((250, 200))
            from PIL import ImageTk
            new_img_tk = ImageTk.PhotoImage(display_image)
            self.img_after_label.configure(image=new_img_tk, text="")
            self.img_after_label.image = new_img_tk  # zapobiega garbage collection
            print("Dane zostały ukryte w obrazie.")
            save_path = filedialog.asksaveasfilename(title="Zapisz nowy obraz jako", defaultextension=".bmp", filetypes=[("BMP Files", "*.bmp")])
            if save_path:
                new_image.save(save_path)
                print(f"Nowy obraz został zapisany jako: {save_path}")
                
                capacity_bytes = calculate_capacity(self.carrier_path, r_bits, g_bits, b_bits)
                self.update_chart_and_stats(capacity_bytes, total_used_bytes)
        except Exception as e:
            print(f"Błąd podczas ukrywania danych: {e}")

    def reveal_data(self):
        print("Odkrywanie danych...")
        self.carrier_path = getattr(self, 'carrier_path', None)
        if not self.carrier_path:
            print("Brak wybranego nośnika!")
            return
        try:
            secret_data, file_extension, r_bits, g_bits, b_bits = decode_data(self.carrier_path)
            
            re_compressed_size = len(zlib.compress(secret_data))
            used_bytes = 64 + re_compressed_size
            print(f"Odkryte dane: {len(secret_data)} bajtów")
            print(f"Rozszerzenie pliku: {file_extension}")
            save_path = filedialog.asksaveasfilename(title="Zapisz odkryty plik jako", defaultextension=file_extension, filetypes=[("", f"*{file_extension}")])
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(secret_data)
                print(f"Odkryty plik został zapisany jako: {save_path}")
                
                capacity_bytes = calculate_capacity(self.carrier_path, r_bits, g_bits, b_bits)
                self.update_chart_and_stats(capacity_bytes, used_bytes)
        except Exception as e:
            print(f"Błąd podczas odkrywania danych: {e}")

    def update_chart_and_stats(self, capacity_bytes, used_bytes):
        free_bytes = max(0, capacity_bytes - used_bytes) # max() ładnie zabezpiecza przed ujemnymi
        
        used_percent = (used_bytes / capacity_bytes) * 100 if capacity_bytes > 0 else 0
        free_percent = 100 - used_percent if used_percent <= 100 else 0

        self.stat_used.configure(text=f"Zajęte miejsce: {format_size(used_bytes)} ({used_percent:.1f}%)")
        self.stat_free.configure(text=f"Wolne miejsce: {format_size(free_bytes)} ({free_percent:.1f}%)")

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        labels = ['Zajęte', 'Wolne']
        sizes = [used_bytes, free_bytes]
        colors = ['#ff6666', '#66b3ff']
        
        if used_bytes > capacity_bytes:
             labels = ['Przekroczenie!']
             sizes = [100]
             colors = ['#ff0000']

        # Rysowanie wykresu
        fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        
        ax.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
            startangle=90, textprops=dict(color="w")
        )
        ax.axis('equal')

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        
        # Zwalnianie pamięci po wygenerowaniu wykresu
        plt.close(fig)