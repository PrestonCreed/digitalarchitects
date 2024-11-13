from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
import logging
from LLMSystem import LLMService, LLMResponse

class ModelType(Enum):
    BUILDING = "building"
    INFRASTRUCTURE = "infrastructure"
    OBJECT = "object"
    POPULATION = "population"

@dataclass
class ProjectContext:
    theme: str
    time_period: str
    environment: str
    existing_structures: List[str]
    special_requirements: Dict[str, Any]

class BaseModelGenerator(ABC):
    """Base class for all model generators"""
    
    def __init__(self, project_context: ProjectContext, llm_service: LLMService):
        self.context = project_context
        self.llm_service = llm_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.analysis_results = {}

    @abstractmethod
    async def analyze_request(self, user_request: str):
        """Analyze user request with type-specific considerations"""
        pass

    @abstractmethod
    def get_analysis_templates(self) -> Dict[str, str]:
        """Get type-specific analysis templates"""
        pass

class BuildingGenerator(BaseModelGenerator):
    """Building-specific generation with detailed analysis steps"""
    
    def get_analysis_templates(self) -> Dict[str, str]:
        return {
            "initial_analysis": """
            Building-Specific Context Analysis:
            1. Building Purpose and Function
               - Primary use cases for the building
               - Expected occupancy and traffic patterns
               - Security and safety requirements
               - Cultural significance in the {time_period}
            
            2. Architectural Style Requirements
               - {time_period} architectural characteristics
               - Regional building traditions
               - Status and prominence considerations
               - Historic accuracy requirements
            """,

            "materials_analysis": """
            Building Materials Analysis:
            1. Exterior Materials
               - Foundation materials (stone, brick, concrete)
               - Wall construction (wood frame, masonry, etc.)
               - Roof materials (shingles, tiles, metal)
               - Weather protection considerations
            
            2. Interior Materials
               - Flooring systems by room type
               - Wall finishing methods
               - Ceiling treatments
               - Trim and decorative elements
            
            3. Game-Ready Material Requirements
               - PBR texture maps needed
               - Material blend maps for wear patterns
               - Optimized material count per section
               - LOD material simplification strategy
            """,

            "spatial_analysis": """
            Building Spatial Analysis:
            1. External Dimensions
               - Footprint calculations
               - Height restrictions
               - Setback requirements
               - Plot orientation
            
            2. Internal Layout
               - Room sizes and arrangements
               - Circulation patterns
               - Functional zones
               - Service area requirements
            
            3. Game Engine Considerations
               - Collision mesh planning
               - Navigation mesh requirements
               - Occlusion culling setup
               - Loading zone boundaries
            """,

            "structural_requirements": """
            Building Structural Requirements:
            1. Core Structure
               - Load-bearing wall placement
               - Support beam systems
               - Foundation requirements
               - Roof structure design
            
            2. Architectural Features
               - Window and door placements
               - Internal wall configurations
               - Stairway and level connections
               - Special feature support
            
            3. Game Implementation
               - Modular construction system
               - Structural LOD planning
               - Physics collision setup
               - Performance optimization zones
            """
        }

class InfrastructureGenerator(BaseModelGenerator):
    """Infrastructure-specific generation with detailed analysis steps"""
    
    def get_analysis_templates(self) -> Dict[str, str]:
        return {
            "initial_analysis": """
            Infrastructure-Specific Context Analysis:
            1. Infrastructure Type and Purpose
               - Network or standalone structure
               - Coverage requirements
               - Flow and connectivity needs
               - Integration with existing systems
            
            2. Environmental Impact
               - Terrain modification needs
               - Natural feature integration
               - Climate considerations
               - Environmental harmony
            """,

            "materials_analysis": """
            Infrastructure Materials Analysis:
            1. Construction Materials
               - Road/path materials
               - Support structure materials
               - Connection point materials
               - Durability requirements
            
            2. Surface Treatments
               - Wear patterns and aging
               - Weather resistance
               - Maintenance considerations
               - Period-appropriate finishes
            
            3. Game-Ready Requirements
               - Seamless texturing systems
               - Tiling optimization
               - Material blending maps
               - Performance optimization
            """,

            "pattern_analysis": """
            Infrastructure Pattern Analysis:
            1. Layout Patterns
               - Grid systems vs organic patterns
               - Connection points
               - Flow optimization
               - Coverage patterns
            
            2. Repetition Strategy
               - Module design
               - Variation implementation
               - Transition handling
               - Pattern optimization
            """,

            "integration_requirements": """
            Infrastructure Integration Requirements:
            1. Connection Points
               - Building interfaces
               - Terrain integration
               - Network connectivity
               - Access points
            
            2. Game Implementation
               - Modular assembly system
               - Procedural generation rules
               - Performance considerations
               - LOD strategy
            """
        }
    
class ObjectGenerator(BaseModelGenerator):
    """Object-specific generation with detailed analysis steps"""
    
    def get_analysis_templates(self) -> Dict[str, str]:
        return {
            "initial_analysis": """
            Object-Specific Context Analysis:
            1. Object Purpose
               - Functional requirements
               - Interactive elements
               - User interaction points
               - Context appropriateness
            
            2. Placement Context
               - Location requirements
               - Surrounding object relationships
               - Access requirements
               - Visibility considerations
            """,

            "materials_analysis": """
            Object Materials Analysis:
            1. Primary Materials
               - Main material types
               - Material properties
               - Wear patterns
               - Age characteristics
            
            2. Detail Materials
               - Decorative elements
               - Hardware and fittings
               - Surface treatments
               - Special effects
            
            3. Game-Ready Requirements
               - Texture efficiency
               - Material count limits
               - LOD material reduction
               - Instance optimization
            """,

            "size_analysis": """
            Object Size Analysis:
            1. Dimensions
               - Core measurements
               - Proportion requirements
               - Scale considerations
               - Clearance needs
            
            2. Variation Planning
               - Size variants needed
               - Scale modifications
               - Proportion adjustments
               - Instance planning
            """,

            "detail_requirements": """
            Object Detail Requirements:
            1. Visual Details
               - Surface detailing
               - Edge treatment
               - Wear and damage
               - Period accuracy
            
            2. Game Implementation
               - LOD planning
               - Collision setup
               - Physics requirements
               - Performance budgets
            """
        }

class PopulationGenerator(BaseModelGenerator):
    """Population-specific generation with detailed analysis steps"""
    
    def get_analysis_templates(self) -> Dict[str, str]:
        return {
            "initial_analysis": """
            Population-Specific Context Analysis:
            1. Space Analysis
               - Area purpose
               - Usage patterns
               - Density requirements
               - Traffic flow
            
            2. Theme Consistency
               - Style requirements
               - Period accuracy
               - Cultural considerations
               - Atmospheric goals
            """,

            "object_analysis": """
            Population Object Analysis:
            1. Object Categories
               - Essential objects
               - Decorative elements
               - Functional items
               - Atmospheric props
            
            2. Distribution Strategy
               - Density patterns
               - Grouping rules
               - Variation requirements
               - Clutter management
            """,

            "placement_strategy": """
            Population Placement Strategy:
            1. Layout Planning
               - Traffic flow paths
               - Functional zones
               - Sight lines
               - Access requirements
            
            2. Variation Planning
               - Object rotation
               - Scale variation
               - Condition variation
               - Distribution patterns
            """,

            "optimization_requirements": """
            Population Optimization Requirements:
            1. Performance Planning
               - Instance batching
               - LOD strategies
               - Draw call optimization
               - Memory management
            
            2. Game Implementation
               - Culling setup
               - Physics optimization
               - Collision handling
               - Loading strategy
            """
        }

class GenerationManager:
    """Manages the model generation process"""
    
    def __init__(self, project_context: ProjectContext, llm_service: LLMService):
        self.context = project_context
        self.llm_service = llm_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def determine_generation_type(self, user_request: str) -> ModelType:
        """Use LLM to determine the type of generation needed"""
        prompt = f"""Analyze this request and determine the type of generation needed:
        Request: {user_request}
        
        Available types:
        - BUILDING (full structures, architecture)
        - INFRASTRUCTURE (roads, paths, networks)
        - OBJECT (individual items, furniture, props)
        - POPULATION (filling spaces with objects)
        
        Respond with just the type name."""

        response = await self.llm_service.process_request(prompt)
        return ModelType[response.analysis.strip()]

    def create_generator(self, model_type: ModelType) -> BaseModelGenerator:
        """Create appropriate generator based on type"""
        generators = {
            ModelType.BUILDING: BuildingGenerator,
            ModelType.INFRASTRUCTURE: InfrastructureGenerator,
            ModelType.OBJECT: ObjectGenerator,
            ModelType.POPULATION: PopulationGenerator
        }
        
        generator_class = generators.get(model_type)
        if not generator_class:
            raise ValueError(f"Unknown model type: {model_type}")
            
        return generator_class(self.context, self.llm_service)

# [Need another part for implementation examples...]