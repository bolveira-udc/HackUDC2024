import tkinter as tk

def process_strings():
    # Obtener los strings ingresados por el usuario
    strings = [entry.get() for entry in entry_list]

    # Destruir todos los widgets en master_frame excepto la salida
    for widget in master_frame.winfo_children():
        if widget != output_label:
            widget.destroy()

    # Mostrar la salida en la etiqueta de salida
    output_label.config(text="Salida procesada: " + ", ".join(strings))

def process_strings_once():
    # Deshabilitar el botón para evitar múltiples clics
    start_button.config(state="disabled")

    # Destruir los widgets de la pantalla de inicio
    start_label.pack_forget()
    start_button.pack_forget()  # Ocultar el botón de inicio

    # Mostrar el texto central y el bloque de texto
    global destination_entry, destination_label, confirm_button
    destination_label = tk.Label(master_frame, text="Indique su destino:", font=("Helvetica", 24), bg="#f0f0f0", fg="#333333")
    destination_label.pack(expand=True)
    
    destination_entry = tk.Entry(master_frame, font=("Helvetica", 24), bg="#ffffff", fg="#333333", justify="center")
    destination_entry.pack(expand=True, fill="x", pady=10)
    
    confirm_button = tk.Button(master_frame, text="Confirmar", command=confirm_destination, font=("Helvetica", 12), bg="#4caf50", fg="#ffffff")
    confirm_button.pack(expand=True, pady=10)

def confirm_destination():
    destination = destination_entry.get()
    destination_label.destroy()
    destination_entry.destroy()
    confirm_button.destroy()

    # Crear etiquetas y campos de entrada para los strings
    global entry_list
    entry_list = []
    for i in range(5):
        frame = tk.Frame(master_frame, bg="#f0f0f0")
        frame.pack(expand=True, fill="x", pady=(5, 2))
        label = tk.Label(frame, text="Localizacion Pesona  {}: ".format(i+1), font=("Helvetica", ), bg="#f0f0f0", fg="#333333")
        label.pack(side="left", padx=(0, 5))
        entry = tk.Entry(frame, font=("Helvetica", 24), bg="#ffffff", fg="#333333")
        entry.pack(side="left", expand=True, fill="x")
        entry_list.append(entry)

    # Crear botón para procesar los strings
    process_button = tk.Button(master_frame, text="Procesar", command=process_strings, font=("Helvetica", 12), bg="#4caf50", fg="#ffffff")
    process_button.pack(expand=True, pady=10)

# Crear ventana principal
root = tk.Tk()
root.title("Interfaz para Procesar Strings")
root.configure(bg="#FF0000")

# Obtener tamaño de la pantalla
window_width = 1280
window_height = 720
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calcular las coordenadas para centrar la ventana en la pantalla
x_coordinate = (screen_width - window_width) // 2
y_coordinate = (screen_height - window_height) // 2

# Definir tamaño de la ventana y centrarla en la pantalla
root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

# Crear un Frame maestro para contener todos los elementos
master_frame = tk.Frame(root, bg="#f0f0f0")
master_frame.pack(expand=True, fill="both", padx=10, pady=10)

# Crear pantalla inicial
start_label = tk.Label(master_frame, text="Rutas Verdes", font=("Helvetica", 76), bg="#f0f0f0", fg="#333333")
start_button = tk.Button(master_frame, text="Start", command=process_strings_once, font=("Helvetica", 18), bg="#4caf50", fg="#ffffff")

start_label.pack(expand=True)
start_button.pack(expand=True, pady=20)

# Etiqueta de salida
output_label = tk.Label(master_frame, text="", font=("Helvetica", 24), bg="#f0f0f0", fg="#333333")
output_label.pack(expand=True)

# Lista para almacenar widgets Entry
entry_list = []

root.mainloop()
