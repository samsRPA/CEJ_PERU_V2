class CEJRep:
    
    def __init__(self):
        pass
    
    def _build_base_query(self) -> str:
        return f"""
              
             SELECT     PI.PROCESO_ID,
                            PI.INSTANCIA_RADICACION,
                            D.DESPACHO_NOMBRE,
                            CASE 
                            WHEN D.DESPACHO_NOMBRE LIKE '%DE PAZ%' THEN 'JUZGADO DE PAZ LETRADO'
                            ELSE 
                                'JUZGADO ESPECIALIZADO'
                            END INSTANCIA,
                            CASE 
                            WHEN D.DESPACHO_NOMBRE LIKE '%CIVIL%' THEN 'CIVIL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%COMERCIAL%' THEN 'COMERCIAL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%DE PAZ%' THEN 'CIVIL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%FAMILIA%' THEN 'FAMILIA'
                            END ESPECIALIDAD,
                            F_REPLACE_CHAR (VM.DEMANDANTE) AS DEMANDANTE,
                                F_REPLACE_CHAR (VM.DEMANDADO) AS DEMANDADO
                    FROM PROCESOS_INSTANCIAS PI, DESPACHOS D , VM_PROCESOS VM , PROCESOS_CLIENTES PC
                    WHERE  PI.PROCESO_ID = VM.PROCESO_ID   
                        AND PI.DESPACHO_ID = D.DESPACHO_ID
                        AND PC.PROCESO_ID = PI.PROCESO_ID
                        AND VM.PROCESO_ID = PC.PROCESO_ID
                        AND D.LOCALIDAD_ID IN (    SELECT LOCALIDAD_ID
                                                        FROM LOCALIDADES
                                                CONNECT BY PRIOR LOCALIDAD_ID = LOCALIDAD_PADRE
                                                START WITH LOCALIDAD_ID = 589)           
                        AND LENGTH(PI.INSTANCIA_RADICACION) > 12 
        """

    async def getAllCaseNumbers(self, conn):
        """Devuelve todos los radicados"""
        query = self._build_base_query()
           
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            return await cursor.fetchall()

    async def getCaseNumber(self, conn, caseNumber: str):
        """Devuelve el  radicado específico."""
        query = self._build_base_query() + """
                and PI.INSTANCIA_RADICACION = :caseNumber  
                
        """
        async with conn.cursor() as cursor:
            await cursor.execute(query, {
                "caseNumber": caseNumber
            })
            return await cursor.fetchone()
