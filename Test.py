import bpy
import bmesh
import mathutils

# Goal
# Create a new object with a water mesh. A water mesh is defined to start 0.1 above the first vcertex in the first
# object of the first scene. From here walk through mesh data and check if the new vertex is on the same level
# or below initial vertex.
#
# Steps
# 1 Get to first vertex [x]
# 2 Create new obejct [x]
# 3 Add object to collcetion [x}
# 4 Fill new object with vertex data / create vertex data [x]
# 5 Walk through exting mesh data
# 6 Extened new obejcts mesh data
# Save and be happy
#
# Goodies
# UI integration ( select start vertex instead of using first found one )

def main():
    water_mesh = bpy.data.meshes.new('waterMesh')
    water_obj = bpy.data.objects.new('water', water_mesh)
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            visited = []
            process = []
            if isinstance(obj.data, bpy.types.Mesh) and obj.data.total_vert_sel > 0:
                water_obj.location = obj.location
                
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                
                bhv_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                
                bpy.ops.object.editmode_toggle()
                verts = get_selected_verts(obj.data)
                new_verts = []
                new_edges = []
                vertex_map = {}
                
                for v in verts:
                    new_verts.append(translate_z(v))
                    new_vert_index = len(new_verts) - 1
                    process.append((v.index, len(new_verts) - 1))
                    vertex_map[v.index] = new_vert_index
                    
                while len(process) > 0:
                    (check_index, base_index) = process.pop()
                    visited.append(check_index)
                    
                    connected_verts = get_connected_verts(obj.data, check_index)
                    for check_vert in connected_verts:
                        obj.data.vertices[check_vert.index].select = True
                        if is_processed(visited, process, check_vert.index) == False:
                            vertex_normal = mathutils.Vector((check_vert.normal[0], check_vert.normal[1], check_vert.normal[2]))
                            res = vertex_normal.dot(mathutils.Vector((0, 0, 1)))
                            if res > 0:
                                new_verts.append(translate_z(check_vert))
                                new_vert_index = len(new_verts) - 1
                                vertex_map[check_vert.index] = new_vert_index
                                process.append((check_vert.index, new_vert_index))
                                if base_index > -1:
                                    new_edges.append([base_index, new_vert_index])
                            else:
                                process.append((check_vert.index, -1))
                        else:
                            if check_vert.index in vertex_map:
                                water_mesh_vert_index = vertex_map[check_vert.index]
                                if (
                                    is_visited(visited, check_vert.index) and
                                    base_index > -1 and
                                    in_edges(new_edges, water_mesh_vert_index, base_index) == False
                                ):
                                    new_edges.append([water_mesh_vert_index, base_index])

                new_faces = []
                old_poly_index_processed = []
                for old_index in vertex_map.keys():
                    for poly in obj.data.polygons:
                        if poly_contains_vert_index(poly, old_index):
                            poly_ok = all(a in vertex_map.keys() for a in poly.vertices)
                            if poly_ok and index_processed(old_poly_index_processed, poly.index) == False:
                                new_poly = create_new_polygon(poly, vertex_map)
                                new_faces.append(new_poly)

                water_mesh.from_pydata(new_verts, new_edges, new_faces)
                water_mesh.calc_normals()



                bpy.ops.object.editmode_toggle()

    bpy.context.collection.objects.link(water_obj)    

def create_new_polygon(poly, old_to_new):
    new_face = []
    for old_vert_index in poly.vertices:
        new_face.append(old_to_new[old_vert_index])
    return new_face

def poly_contains_vert_index(poly, vert_index):
    for old_vert_index in poly.vertices:
        if vert_index == old_vert_index:
            return True
    return False

def index_processed(old_poly_index_processed, index):
    for check in old_poly_index_processed:
        if check == index:
            return True
    return False

def is_visited(visited, index):
    for check in visited:
        if check == index:
            return True
    return False

def in_edges(edges, index1, index2):
    for [check1, check2] in edges:
        if (check1 == index1 or check1 == index2) and (check2 == index1 or check2 == index2):
            return True
    return False

def is_processed(visited, process, index):
    for check in visited:
        if check == index:
            return True
    for check in process:
        if check == index:
            return True
    return False
                
def get_selected_verts(mesh):
    verts = []
    for vert in mesh.vertices:
        if vert.select == True:
            verts.append(vert)
    return verts

def translate_z(vert):
    v = mathutils.Vector((vert.co[0], vert.co[1], vert.co[2]))
    return v + mathutils.Vector((vert.normal[0], vert.normal[1], vert.normal[2])) * 0.3

def get_connected_verts(mesh, vertex_index):
    connection_indices = []
    for edge in mesh.edges:
        if edge.vertices[0] == vertex_index:
            connection_indices.append(edge.vertices[1])
        if edge.vertices[1] == vertex_index:
            connection_indices.append(edge.vertices[0])
            
    connections = []
    for index in connection_indices:
        connections.append(mesh.vertices[index])

    return connections

if __name__ == "__main__":
    main()
    