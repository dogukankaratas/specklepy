from specklepy.objects.geometry import Line, Polyline, Mesh
from specklepy.objects.base import Base
from typing import List, Optional
import math

GEOMETRY = "Objects.Geometry."

class RebarRepresentationMode:
    AS_LINE = "AsLine"
    AS_VOLUME = "AsVolume"

class RebarGroup(Base, speckle_type=GEOMETRY + "RebarGroup"):
    def __init__(self, 
                 shape: 'RebarShape', 
                 number: int, 
                 has_first_bar: bool = True, 
                 has_last_bar: bool = True, 
                 start_hook: Optional['RebarHook'] = None, 
                 end_hook: Optional['RebarHook'] = None, 
                 volume: float = 0.0, 
                 units: str = 'meters', 
                 representation_mode: str = RebarRepresentationMode.AS_LINE):
        super().__init__()
        self.shape = shape
        self.number = number
        self.has_first_bar = has_first_bar
        self.has_last_bar = has_last_bar
        self.start_hook = start_hook
        self.end_hook = end_hook
        self.volume = volume
        self.units = units
        self.representation_mode = representation_mode
        
        self.representation = self.generate_representation()
    
    def generate_representation(self) -> List[Base]:
        '''
        master function to generate representation of the rebar
        '''
        if self.representation_mode == RebarRepresentationMode.AS_VOLUME:
            return self._generate_volumetric_representation()
        else:
            return self._generate_line_representation()
    
    def _generate_line_representation(self) -> List[Line]:
        '''
        internal method to apply representation to rebar group
        '''
        lines = []
        for i in range(self.number):
            for line in self.shape.lines:
                lines.append(line)
            for polyline in self.shape.polylines:
                for j in range(0, len(polyline.value) - 3, 3):
                    start_point = polyline.value[j:j+3]
                    end_point = polyline.value[j+3:j+6]
                    lines.append(Line(start=start_point, end=end_point))
        return lines

    def _generate_volumetric_representation(self) -> List[Mesh]:
        '''
        logic to transform line representation to volumetric mesh
        '''
        meshes = []
        for i in range(self.number):
            for line in self.shape.lines:
                mesh = self._line_to_cylinder_mesh(line)
                meshes.append(mesh)
            for polyline in self.shape.polylines:
                for j in range(0, len(polyline.value) - 3, 3):
                    start_point = polyline.value[j:j+3]
                    end_point = polyline.value[j+3:j+6]
                    mesh = self._line_to_cylinder_mesh(Line(start=start_point, end=end_point))
                    meshes.append(mesh)
        return meshes
    
    def _line_to_cylinder_mesh(self, line: Line, num_segments: int = 36) -> Mesh:
        vertices = []
        faces = []

        start_point = [line.start.x, line.start.y, line.start.z]
        end_point = [line.end.x, line.end.y, line.end.z]

        radius = self.shape.bar_diameter / 2000

        direction = [end_point[i] - start_point[i] for i in range(3)]
        length = math.sqrt(sum(d ** 2 for d in direction))

        unit_direction = [d / length for d in direction]

        circle_vertices = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            circle_vertices.append([x, y, 0])

        for vertex in circle_vertices:
            vertices.extend([
                start_point[0] + vertex[0],
                start_point[1] + vertex[1],
                start_point[2]
            ])
            vertices.extend([
                start_point[0] + vertex[0] + length * unit_direction[0],
                start_point[1] + vertex[1] + length * unit_direction[1],
                start_point[2] + length * unit_direction[2]
            ])

        for i in range(num_segments):
            bottom1 = i * 2
            top1 = bottom1 + 1
            bottom2 = (i * 2 + 2) % (num_segments * 2)
            top2 = (i * 2 + 3) % (num_segments * 2)

            faces.extend([3, bottom1, top1, bottom2])
            faces.extend([3, top1, top2, bottom2])

        top_center = len(vertices) // 2 - 1
        bottom_center = len(vertices) - 1

        for i in range(num_segments):
            faces.extend([3, bottom_center, i * 2, (i * 2 + 2) % (num_segments * 2)])
            faces.extend([3, top_center, (i * 2 + 1) % (num_segments * 2), i * 2 + 1])

        mesh = Mesh(vertices=vertices, faces=faces)
        return mesh

class RebarShape(Base):
    def __init__(self, 
                 name: str, 
                 rebar_type: 'RebarType', 
                 lines: Optional[List[Line]] = None, 
                 polylines: Optional[List[Polyline]] = None, 
                 bar_diameter: float = 0.0, 
                 units: str = 'meters'):
        super().__init__()
        self.name = name
        self.rebar_type = rebar_type
        self.lines = lines or []
        self.polylines = polylines or []
        self.bar_diameter = bar_diameter
        self.units = units

class RebarHook(Base):
    def __init__(self, 
                 angle: float = 0.0, 
                 length: float = 0.0, 
                 radius: float = 0.0, 
                 units: str = 'meters'):
        super().__init__()
        self.angle = angle
        self.length = length
        self.radius = radius
        self.units = units
        
class RebarType:
    UNKNOWN = "Unknown"
    STANDARD = "Standard"
    STIRRUP_POLYGONAL = "StirrupPolygonal"
    STIRRUP_SPIRAL = "StirrupSpiral"
    STIRRUP_TAPERED = "StirrupTapered"

class Rebar(Base):
    def __init__(self, 
                 lines: Optional[List[Line]] = None, 
                 polylines: Optional[List[Polyline]] = None, 
                 volume: float = 0.0, 
                 units: str = 'meters'):
        super().__init__()
        self.lines = lines or []
        self.polylines = polylines or []
        self.volume = volume
        self.units = units
