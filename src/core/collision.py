
import pygame
import math

class SAT:
    """Implementasi Separating Axis Theorem (SAT) untuk deteksi tabrakan Poligon."""
    
    @staticmethod
    def get_axes(points):
        axes = []
        for i in range(len(points)):
            p1 = pygame.math.Vector2(points[i])
            p2 = pygame.math.Vector2(points[(i + 1) % len(points)])
            edge = p2 - p1
            # Perpendicular (Normal)
            normal = pygame.math.Vector2(-edge.y, edge.x)
            if normal.magnitude() > 0:
                axes.append(normal.normalize())
        return axes

    @staticmethod
    def project(points, axis):
        min_proj = float('inf')
        max_proj = float('-inf')
        for p in points:
            proj = axis.dot(pygame.math.Vector2(p))
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        return min_proj, max_proj

    @staticmethod
    def is_overlapping(proj1, proj2):
        return proj1[0] <= proj2[1] and proj2[0] <= proj1[1]

    @staticmethod
    def collides(poly1, poly2):
        """
        Deteksi tabrakan antara dua daftar titik (poligon).
        Bisa berupa daftar (x,y) atau pygame.Rect (akan dikonversi).
        """
        # Konversi Rect ke daftar titik jika perlu
        if isinstance(poly1, pygame.Rect):
            poly1 = [poly1.topleft, poly1.topright, poly1.bottomright, poly1.bottomleft]
        if isinstance(poly2, pygame.Rect):
            poly2 = [poly2.topleft, poly2.topright, poly2.bottomright, poly2.bottomleft]

        if not poly1 or not poly2: return False

        axes = SAT.get_axes(poly1) + SAT.get_axes(poly2)
        
        for axis in axes:
            proj1 = SAT.project(poly1, axis)
            proj2 = SAT.project(poly2, axis)
            if not SAT.is_overlapping(proj1, proj2):
                return False # Separating axis ditemukan!
        
        return True # Tidak ada sumbu pemisah
