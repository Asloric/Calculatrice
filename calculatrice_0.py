import tkinter as tk
import re

class MagicCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Magic Calculator")
        
        # Zone de texte pour entrer les formules et afficher les calculs
        self.text_area = tk.Text(self, width=50, height=20)
        self.text_area.grid(row=0, column=0, padx=10, pady=10)
        self.text_area.bind('<<Modified>>', self.on_text_change)
        self.text_area.bind('<Return>', self.on_text_change)
        
        # Liste pour afficher les résultats
        self.result_list = tk.Listbox(self, width=30, height=20)
        self.result_list.grid(row=0, column=1, padx=10, pady=10)
        self.result_list.bind("<<ListboxSelect>>", self.on_result_selected)
        
        self.results = []
        self.formulas = []

    def on_text_change(self, event=None):
        # Désactiver l'événement <<Modified>> temporairement pour éviter les boucles infinies
        # self.text_area.unbind('<<Modified>>')
        
        # Identifier les modifications
        cursor_index = self.text_area.index(tk.INSERT)
        line_number = int(cursor_index.split('.')[0]) - 1
        line_start_index = f"{line_number + 1}.0"
        line_end_index = f"{line_number + 1}.end"
        lines_after_cursor = self.text_area.get(cursor_index, "end-1c")
        
        # Obtenir le texte complet de la ligne
        line_text = self.text_area.get(line_start_index, line_end_index).strip()

        if line_text:
            if event.keycode == 13: 
                try:
                    # Remplacer "ans(x)" par les valeurs précédentes
                    formula = self.replace_ans(line_text, line_number)
                    
                    # Calculer le résultat
                    result = eval(formula)
                    
                    # Mettre à jour la formule et le résultat
                    if line_number < len(self.formulas):
                        self.formulas[line_number] = line_text
                        self.results[line_number] = result
                    else:
                        self.formulas.append(line_text)
                        self.results.append(result)
                    
                    # Mettre à jour la liste des résultats
                    self.update_results_list()
                    
                    # Ajouter le résultat dans la zone de texte
                    self.text_area.delete(line_start_index, line_end_index)
                    self.text_area.insert(line_start_index, f"{line_text}")
                    
                    # Mettre à jour les résultats en cascade
                    self.update_cascade(0)
                    
                except Exception as e:
                    # Mettre à jour la formule et le résultat
                    if line_number < len(self.formulas):
                        self.formulas[line_number] = line_text
                        self.results[line_number] = "error"
                    else:
                        self.formulas.append(line_text)
                        self.results.append("error")
                    
                    # Mettre à jour la liste des résultats
                    self.update_results_list()
                    
                    # Ajouter le résultat dans la zone de texte
                    self.text_area.delete(line_start_index, line_end_index)
                    self.text_area.insert(line_start_index, f"{line_text}")
                    
                    # Mettre à jour les résultats en cascade
                    self.update_cascade(0)
            else:
                # Remplacer "ans(x)" par les valeurs précédentes
                formula = self.replace_ans(line_text, line_number)
                
                # Calculer le résultat
                result = eval(formula)
                
                # Mettre à jour la formule et le résultat
                if line_number < len(self.formulas):
                    self.formulas[line_number] = line_text
                    self.results[line_number] = result
                else:
                    self.formulas.append(line_text)
                    self.results.append(result)
                
                # Mettre à jour la liste des résultats
                self.update_results_list()
                self.update_cascade(0)

        # Réactiver l'événement <<Modified>>
        self.text_area.bind('<<Modified>>', self.on_text_change)
        if event.keycode == 13 and lines_after_cursor:
            return "break" 
            
    
    def replace_ans(self, formula, line_number):
        # Vérifier si la formule commence par un opérateur mathématique
        if re.match(r"^[\+\-\*/\^]", formula):
            formula = f"ans({line_number-1})" + formula

        # Remplacer toutes les occurrences de "ans(x)" par les résultats correspondants
        for i in range(len(self.results)):
            formula = formula.replace(f"ans({i})", str(self.results[i]))
        return formula

    def update_results_list(self):
        # Effacer la liste actuelle des résultats
        self.result_list.delete(0, tk.END)
        # Ajouter les résultats mis à jour
        for i, result in enumerate(self.results):
            self.result_list.insert(tk.END, f"{i}: {result}")

    def update_cascade(self, start_index):
        for i in range(start_index, len(self.results)):
            try:
                # Obtenir la formule de la ligne actuelle de la zone de texte
                line_start_index = f"{i + 1}.0"
                line_end_index = f"{i + 1}.end"
                line_text = self.text_area.get(line_start_index, line_end_index).strip()
                
                # Remplacer les "ans(x)" dans la formule par les résultats correspondants
                formula = self.replace_ans(line_text, i)
                
                # Calculer le résultat
                result = eval(formula)
                
                # Mettre à jour le résultat
                self.results[i] = result
                
                # Si la ligne actuelle n'est pas vide, la remplacer par son contenu mis à jour
                if line_text:
                    self.text_area.delete(line_start_index, line_end_index)
                    self.text_area.insert(line_start_index, f"{line_text}")

            except Exception as e:
                # S'il y a une erreur lors du calcul, enregistrer "error" comme résultat
                self.results[i] = "error"
                if line_text:
                    self.text_area.delete(line_start_index, line_end_index)
                    self.text_area.insert(line_start_index, f"{line_text}")

        # Mettre à jour la liste des résultats
        self.update_results_list()

    
    def on_result_selected(self, event):
        # Récupérer l'index de l'élément sélectionné dans la liste des résultats
        selected_index = self.result_list.curselection()[0]
        # Insérer "ans(x)" à la position du curseur dans la zone de texte
        self.text_area.insert(tk.INSERT, f"ans({selected_index})")

if __name__ == "__main__":
    app = MagicCalculator()
    app.mainloop()
